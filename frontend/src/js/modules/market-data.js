import {
  ApiRequestError,
  attachMarketReference,
  decideMarketDataSnapshot,
  fetchMarketDataCandidate,
  getCurrentUser,
  getMarketDataProviders,
  getMarketDataSnapshots,
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

function renderProviders(container, providers, onFetch) {
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
    const button = document.createElement("button"); button.type = "button"; button.className = "btn btn-primary"; button.textContent = "Отримати кандидат";
    button.addEventListener("click", () => onFetch(provider.provider_code, button));
    card.append(title, note, links, button); container.append(card);
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
  const snapshots = document.getElementById("market-data-snapshots");
  const form = document.getElementById("market-reference-attach-form");
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
    const [providerRows, snapshotRows] = await Promise.all([getMarketDataProviders(token), getMarketDataSnapshots(token)]);
    currentSnapshots = snapshotRows;
    renderProviders(providers, providerRows, async (providerCode, button) => {
      button.disabled = true;
      try { setStatus(status, "Отримання даних OpenFacet…"); await fetchMarketDataCandidate(providerCode, token); setStatus(status, "Створено кандидат. Перевірте покриття та затвердьте його окремо."); await refresh(); }
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
      setStatus(status, `Додано ринковий орієнтир: ${valuation.currency_code} ${Number(valuation.amount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.`);
      form.reset(); updateApprovedSnapshotOptions(snapshotSelect, currentSnapshots);
    } catch (error) { setStatus(status, error.message || "Не вдалося прикріпити ринковий орієнтир.", true); }
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
