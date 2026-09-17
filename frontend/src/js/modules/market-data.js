import {
  ApiRequestError,
  attachMarketReference,
  decideMarketDataSnapshot,
  fetchMarketDataCandidate,
  getCurrentUser,
  getMarketDataProviders,
  getMarketReferencePolicy,
  getMarketDataSnapshots,
  getFxDataSnapshots,
  refreshNbuRate,
  updateMarketReferencePolicy,
} from "./api.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";

const STATUS_LABELS = { candidate: "Кандидат", approved: "Затверджено", rejected: "Відхилено" };

function formatDate(value) {
  return value ? new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
}

function setStatus(node, message, isError = false) {
  node.textContent = message;
  node.classList.toggle("is-error", isError);
  node.hidden = false;
}

function marketReferenceMessage(error) {
  const messages = {
    "OpenFacet reference is available only for natural stones": "OpenFacet у цьому контурі доступний лише для каменів із походженням «Природний». Для лабораторно вирощеного каменю орієнтир не створено.",
    "The report lacks characteristics required by the selected market snapshot": "У звіті бракує характеристик, потрібних для зіставлення з обраним знімком OpenFacet.",
    "The approved snapshot does not cover this shape, color or clarity": "Обраний знімок OpenFacet не має покриття для цієї форми, кольору або чистоти.",
    "The approved snapshot does not cover this carat weight": "Обраний знімок OpenFacet не має покриття для цієї ваги в каратах.",
    "This approved snapshot is already attached to the report": "Цей затверджений знімок уже прикріплено до звіту.",
  };
  return messages[error?.message] || error?.message || "Не вдалося прикріпити ринковий орієнтир.";
}

function renderProviders(container, providers, fxSnapshots, onAction) {
  container.replaceChildren();
  for (const provider of providers) {
    const card = document.createElement("article");
    card.className = "market-data-card";
    const title = document.createElement("h3"); title.textContent = provider.display_name;
    const note = document.createElement("p"); note.textContent = provider.scope_note;
    const links = document.createElement("p");
    for (const [href, text] of [[provider.documentation_url, "Документація"], [provider.terms_url, "Умови використання"]]) {
      const link = document.createElement("a"); link.href = href; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = text;
      links.append(link, document.createTextNode(" · "));
    }
    links.lastChild.remove();
    const isNbu = provider.provider_code === "nbu";
    if (isNbu) {
      const latest = fxSnapshots[0];
      const rate = document.createElement("p");
      rate.textContent = latest
        ? `Останній знімок: 1 USD = ${Number(latest.rate).toLocaleString("uk-UA", { minimumFractionDigits: 2, maximumFractionDigits: 4 })} UAH · офіційна дата ${new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(`${latest.rate_date}T00:00:00`))}.`
        : "Знімків курсу ще немає. Під час прикріплення орієнтира курс також отримується автоматично.";
      card.append(rate);
    }
    const button = document.createElement("button"); button.type = "button"; button.className = "btn btn-primary";
    button.textContent = isNbu ? "Оновити зараз" : "Отримати кандидат";
    button.addEventListener("click", () => onAction(provider.provider_code, button));
    card.append(title, note, links, button); container.append(card);
  }
}

function renderPolicyMarketProviders(container, providers, selectedProviderCode) {
  container.replaceChildren();
  const marketProviders = providers.filter((provider) => provider.provider_type === "market_reference");
  if (!marketProviders.length) {
    container.textContent = "Активних провайдерів ринкового орієнтиру немає.";
    return;
  }
  for (const provider of marketProviders) {
    const label = document.createElement("label");
    label.className = "market-policy-option";
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "market-policy-provider";
    input.value = provider.provider_code;
    input.checked = provider.provider_code === selectedProviderCode;
    const text = document.createElement("span");
    text.textContent = `${provider.display_name} — ${provider.scope_note}`;
    label.append(input, text);
    container.append(label);
  }
}

function renderSnapshots(container, snapshots, onDecision) {
  container.replaceChildren();
  if (!snapshots.length) {
    const empty = document.createElement("p"); empty.className = "account-help"; empty.textContent = "Знімків ще немає."; container.append(empty); return;
  }
  for (const snapshot of snapshots) {
    const card = document.createElement("article"); card.className = "market-data-card";
    const title = document.createElement("h3"); title.textContent = `${snapshot.provider_code} · ${STATUS_LABELS[snapshot.status] || snapshot.status}`;
    const meta = document.createElement("p"); meta.textContent = `${snapshot.quote_count} котирувань · ${snapshot.currency_code} · ${snapshot.unit} · отримано ${formatDate(snapshot.retrieved_at)}`;
    const scope = document.createElement("p"); scope.textContent = snapshot.coverage_note;
    const source = document.createElement("a"); source.href = snapshot.methodology_url; source.target = "_blank"; source.rel = "noopener noreferrer"; source.textContent = "Методологія джерела";
    card.append(title, meta, scope, source);
    if (snapshot.decision_reason) { const decision = document.createElement("p"); decision.textContent = `Рішення: ${snapshot.decision_reason}`; card.append(decision); }
    if (snapshot.status === "candidate") {
      const actions = document.createElement("div"); actions.className = "market-data-card__actions";
      for (const [action, label, className] of [["approve", "Затвердити", "btn btn-primary"], ["reject", "Відхилити", "btn btn-outline"]]) {
        const button = document.createElement("button"); button.type = "button"; button.className = className; button.textContent = label;
        button.addEventListener("click", () => onDecision(snapshot.snapshot_id, action)); actions.append(button);
      }
      card.append(actions);
    }
    container.append(card);
  }
}

function updateApprovedSnapshotOptions(select, snapshots) {
  const approved = snapshots.filter((snapshot) => snapshot.status === "approved");
  select.replaceChildren();
  const placeholder = document.createElement("option"); placeholder.value = ""; placeholder.textContent = approved.length ? "Оберіть знімок" : "Немає затверджених знімків";
  select.append(placeholder);
  for (const snapshot of approved) {
    const option = document.createElement("option"); option.value = snapshot.snapshot_id;
    option.textContent = `#${snapshot.snapshot_id} · ${snapshot.provider_code} · ${formatDate(snapshot.retrieved_at)}`;
    select.append(option);
  }
  select.disabled = !approved.length;
}

export async function initMarketData() {
  const page = document.querySelector("[data-market-data-page]");
  if (!page) return;
  const token = localStorage.getItem("token");
  const status = document.getElementById("market-data-status");
  const providers = document.getElementById("market-data-providers");
  const policyForm = document.getElementById("market-reference-policy-form");
  const policyProviders = document.getElementById("market-policy-market-providers");
  const policyUseFx = document.getElementById("market-policy-use-fx");
  const policyFxNote = document.getElementById("market-policy-fx-note");
  const policySubmit = document.getElementById("market-reference-policy-submit");
  const snapshots = document.getElementById("market-data-snapshots");
  const form = document.getElementById("market-reference-attach-form");
  const referenceStatus = document.getElementById("market-reference-status");
  const snapshotSelect = document.getElementById("market-reference-snapshot");
  const decisionDialog = document.getElementById("market-decision-dialog");
  const decisionForm = document.getElementById("market-decision-form");
  const decisionDescription = document.getElementById("market-decision-dialog-description");
  const decisionReasonLabel = document.getElementById("market-decision-reason-label");
  const decisionReason = document.getElementById("market-decision-reason");
  const decisionSubmit = document.getElementById("market-decision-submit");
  let currentSnapshots = [];
  let pendingDecision = null;
  const closeDecisionDialog = () => { pendingDecision = null; decisionForm.reset(); decisionDialog.close(); };
  const openDecisionDialog = (snapshotId, action) => {
    pendingDecision = { snapshotId, action };
    const isApproval = action === "approve";
    decisionDescription.textContent = isApproval
      ? "Після затвердження цей незмінний знімок можна буде явно прикріпити до сумісного звіту."
      : "Відхилений знімок не можна використати для ринкового орієнтира; самі дані знімка лишаться в історії.";
    decisionReasonLabel.textContent = isApproval ? "Коментар до затвердження" : "Причина відхилення";
    decisionReason.placeholder = isApproval ? "Необов’язково" : "Необов’язково";
    decisionSubmit.textContent = isApproval ? "Затвердити знімок" : "Відхилити знімок";
    decisionDialog.showModal();
    decisionReason.focus();
  };
  const refresh = async () => {
    const [providerRows, policy, snapshotRows, fxSnapshotRows] = await Promise.all([getMarketDataProviders(token), getMarketReferencePolicy(token), getMarketDataSnapshots(token), getFxDataSnapshots(token)]);
    currentSnapshots = snapshotRows;
    renderPolicyMarketProviders(policyProviders, providerRows, policy.market_provider_code);
    policyUseFx.checked = policy.use_fx_conversion;
    const fxProvider = providerRows.find((provider) => provider.provider_code === policy.fx_provider_code);
    policyFxNote.textContent = policy.use_fx_conversion
      ? `Курс ${fxProvider?.display_name || "валютного провайдера"} фіксується лише разом із новим орієнтиром.`
      : "Еквівалент у UAH для нових орієнтирів не створюватиметься.";
    renderProviders(providers, providerRows, fxSnapshotRows, async (providerCode, button) => {
      button.disabled = true;
      try {
        if (providerCode === "nbu") {
          setStatus(status, "Отримання офіційного курсу НБУ…");
          await refreshNbuRate(token);
          setStatus(status, "Новий незмінний знімок офіційного курсу НБУ збережено.");
        } else {
          setStatus(status, "Отримання даних OpenFacet…");
          await fetchMarketDataCandidate(providerCode, token);
          setStatus(status, "Створено кандидат. Перевірте покриття та затвердьте його окремо.");
        }
        await refresh();
      }
      catch (error) { setStatus(status, error.message || "Не вдалося отримати дані провайдера.", true); }
      finally { button.disabled = false; }
    });
    renderSnapshots(snapshots, snapshotRows, openDecisionDialog);
    updateApprovedSnapshotOptions(snapshotSelect, snapshotRows);
  };
  try {
    const user = await getCurrentUser(token);
    if (user.role !== "admin") throw new Error("Ця сторінка доступна лише адміністратору.");
    await refresh();
  } catch (error) {
    setStatus(status, error instanceof ApiRequestError && error.status === 401 ? "Потрібно увійти знову." : error.message, true);
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    try {
      const valuation = await attachMarketReference(
        document.getElementById("market-reference-report-id").value.trim(),
        { snapshot_id: Number(snapshotSelect.value), applicability_confirmed: true, applicability_note: document.getElementById("market-reference-note").value.trim() }, token,
      );
      const converted = valuation.converted_amount
        ? ` ≈ ${valuation.converted_currency_code} ${Number(valuation.converted_amount).toLocaleString("uk-UA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.`
        : "";
      setStatus(status, `Додано ринковий орієнтир: ${valuation.currency_code} ${Number(valuation.amount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.${converted}`);
      setStatus(referenceStatus, "Ринковий орієнтир успішно прикріплено.");
      form.reset(); updateApprovedSnapshotOptions(snapshotSelect, currentSnapshots);
    } catch (error) {
      const message = marketReferenceMessage(error);
      setStatus(status, message, true);
      setStatus(referenceStatus, message, true);
    }
  });
  policyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const selectedProvider = policyForm.querySelector('input[name="market-policy-provider"]:checked');
    if (!selectedProvider) {
      setStatus(status, "Оберіть провайдера ринкового орієнтиру.", true);
      return;
    }
    policySubmit.disabled = true;
    try {
      await updateMarketReferencePolicy({
        market_provider_code: selectedProvider.value,
        use_fx_conversion: policyUseFx.checked,
        fx_provider_code: policyUseFx.checked ? "nbu" : null,
      }, token);
      setStatus(status, "Налаштування системного довідкового орієнтиру збережено для майбутніх чернеток.");
      await refresh();
    } catch (error) {
      setStatus(status, error.message || "Не вдалося зберегти налаштування.", true);
    } finally {
      policySubmit.disabled = false;
    }
  });
  document.getElementById("market-decision-dialog-close").addEventListener("click", closeDecisionDialog);
  document.getElementById("market-decision-cancel").addEventListener("click", closeDecisionDialog);
  decisionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!pendingDecision) return;
    const { snapshotId, action } = pendingDecision;
    decisionSubmit.disabled = true;
    try {
      await decideMarketDataSnapshot(snapshotId, action, decisionReason.value.trim(), token);
      closeDecisionDialog();
      setStatus(status, action === "approve" ? "Знімок затверджено." : "Знімок відхилено.");
      await refresh();
    } catch (error) {
      setStatus(status, error.message || "Не вдалося зберегти рішення.", true);
    } finally {
      decisionSubmit.disabled = false;
    }
  });
  registerVisibleDataRefresh(refresh, { canRefresh: () => !form.matches(":focus-within") });
}
