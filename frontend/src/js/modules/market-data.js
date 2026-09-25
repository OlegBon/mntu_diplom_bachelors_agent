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
  getMarketProviderOperations,
  getMarketProviderSchedules,
  refreshNbuRate,
  updateMarketProviderSchedule,
  updateMarketReferencePolicy,
} from "./api.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";

const STATUS_LABELS = { candidate: "Кандидат", approved: "Затверджено", rejected: "Відхилено" };
const FRESHNESS_LABELS = { fresh: "Актуальні", warning: "Потребують оновлення", stale: "Застарілі", missing: "Знімків немає" };
const OPERATION_STATUS_LABELS = { success: "Успішно", no_change: "Без змін", failed: "Помилка", skipped: "Пропущено" };

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

function renderPolicyMarketProviders(container, providers, enabledProviderCodes, primaryProviderCode) {
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
    input.type = "checkbox";
    input.name = "market-policy-provider";
    input.value = provider.provider_code;
    input.checked = enabledProviderCodes.includes(provider.provider_code);
    const primary = document.createElement("input");
    primary.type = "radio";
    primary.name = "market-policy-primary-provider";
    primary.value = provider.provider_code;
    primary.checked = provider.provider_code === primaryProviderCode;
    primary.disabled = !input.checked;
    input.addEventListener("change", () => {
      primary.disabled = !input.checked;
      if (!input.checked) primary.checked = false;
    });
    const text = document.createElement("span");
    text.textContent = `${provider.display_name} — ${provider.scope_note}`;
    const primaryText = document.createElement("span");
    primaryText.textContent = " Основний для списку звітів";
    label.append(input, text, primary, primaryText);
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

function formatScheduleTime(schedule) {
  return `${String(schedule.scheduled_hour).padStart(2, "0")}:${String(schedule.scheduled_minute).padStart(2, "0")}`;
}

function renderSchedules(container, schedules, onSubmit) {
  container.replaceChildren();
  if (!schedules.length) {
    container.textContent = "Графіки ще не створені. Застосуйте міграцію 0013_market_provider_operations.";
    return;
  }
  for (const schedule of schedules) {
    const form = document.createElement("form");
    form.className = "market-data-card";
    form.noValidate = true;
    const title = document.createElement("h3"); title.textContent = schedule.provider_code === "nbu" ? "НБУ" : "OpenFacet";
    const freshness = document.createElement("p");
    freshness.textContent = `Стан даних: ${FRESHNESS_LABELS[schedule.freshness_status] || schedule.freshness_status}${schedule.latest_retrieved_at ? ` · останнє отримання ${formatDate(schedule.latest_retrieved_at)}` : ""}.`;
    const enabled = document.createElement("input"); enabled.type = "checkbox"; enabled.checked = schedule.enabled;
    const enabledLabel = document.createElement("label"); enabledLabel.className = "market-data-confirmation"; enabledLabel.append(enabled, document.createTextNode("Увімкнути планове оновлення"));
    const time = document.createElement("input"); time.type = "time"; time.className = "form-control"; time.value = formatScheduleTime(schedule);
    const warn = document.createElement("input"); warn.type = "number"; warn.className = "form-control"; warn.min = "1"; warn.max = "2160"; warn.value = schedule.warn_after_hours;
    const block = document.createElement("input"); block.type = "number"; block.className = "form-control"; block.min = "1"; block.max = "4320"; block.value = schedule.block_after_hours;
    const fields = document.createElement("div"); fields.className = "form-row";
    for (const [labelText, input] of [["Час (Europe/Kyiv)", time], ["Попереджати через, год.", warn], ["Блокувати через, год.", block]]) {
      const group = document.createElement("div"); group.className = "form-group";
      const label = document.createElement("label"); label.textContent = labelText; label.append(input); group.append(label); fields.append(group);
    }
    const submit = document.createElement("button"); submit.type = "submit"; submit.className = "btn btn-outline"; submit.textContent = "Зберегти графік";
    form.append(title, freshness, enabledLabel, fields, submit);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const [hour, minute] = time.value.split(":").map(Number);
      const payload = {
        provider_code: schedule.provider_code, enabled: enabled.checked, scheduled_hour: hour,
        scheduled_minute: minute, warn_after_hours: Number(warn.value), block_after_hours: Number(block.value),
      };
      if (!time.value || !Number.isInteger(hour) || !Number.isInteger(minute) || payload.block_after_hours < payload.warn_after_hours) {
        onSubmit(null, "Перевірте час і пороги: блокування не може бути раніше попередження.");
        return;
      }
      submit.disabled = true;
      try { await onSubmit(payload); } finally { submit.disabled = false; }
    });
    container.append(form);
  }
}

function renderOperations(container, operations) {
  container.replaceChildren();
  if (!operations.length) {
    container.textContent = "Операцій ще не було.";
    return;
  }
  for (const operation of operations) {
    const item = document.createElement("article"); item.className = "market-data-card";
    const title = document.createElement("h3");
    title.textContent = `${operation.provider_code} · ${OPERATION_STATUS_LABELS[operation.status] || operation.status}`;
    const details = document.createElement("p");
    details.textContent = `${operation.trigger_type === "manual" ? "Вручну" : "За графіком"} · спроба ${operation.attempt_number} · ${formatDate(operation.completed_at)}.`;
    item.append(title, details);
    if (operation.message) { const message = document.createElement("p"); message.textContent = operation.message; item.append(message); }
    container.append(item);
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
  const schedules = document.getElementById("market-provider-schedules");
  const operations = document.getElementById("market-provider-operations");
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
    const [providerRows, policy, snapshotRows, fxSnapshotRows, scheduleRows, operationRows] = await Promise.all([
      getMarketDataProviders(token), getMarketReferencePolicy(token), getMarketDataSnapshots(token), getFxDataSnapshots(token),
      getMarketProviderSchedules(token).catch(() => []), getMarketProviderOperations(token).catch(() => []),
    ]);
    currentSnapshots = snapshotRows;
    renderPolicyMarketProviders(
      policyProviders, providerRows, policy.enabled_market_provider_codes || [],
      policy.dashboard_primary_provider_code || null,
    );
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
    renderSchedules(schedules, scheduleRows, async (payload, validationError) => {
      if (validationError) { setStatus(status, validationError, true); return; }
      try {
        await updateMarketProviderSchedule(payload.provider_code, payload, token);
        setStatus(status, "Графік оновлення збережено.");
        await refresh();
      } catch (error) { setStatus(status, error.message || "Не вдалося зберегти графік.", true); }
    });
    renderOperations(operations, operationRows);
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
    const enabledProviderCodes = [...policyForm.querySelectorAll('input[name="market-policy-provider"]:checked')]
      .map((input) => input.value);
    const primaryProvider = policyForm.querySelector('input[name="market-policy-primary-provider"]:checked');
    if (primaryProvider && !enabledProviderCodes.includes(primaryProvider.value)) {
      setStatus(status, "Основний провайдер має входити до увімкненого набору.", true);
      return;
    }
    policySubmit.disabled = true;
    try {
      await updateMarketReferencePolicy({
        enabled_market_provider_codes: enabledProviderCodes,
        dashboard_primary_provider_code: primaryProvider?.value || null,
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
