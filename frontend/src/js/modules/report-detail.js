import {
  ApiRequestError,
  getCurrentUser,
  getDomainReport,
  getGradeMappings,
  getReportEvents,
  getReportMedia,
  getReportMediaContentUrl,
  getReportPassport,
  getReportPassportQr,
  publishReportPassport,
  reissueReportPassport,
  revokeReportPassport,
  transitionDomainReport,
  updateDomainReport,
} from "./api.js";
import { logout } from "./auth.js";

const STATUS_LABELS = { draft: "Чернетка", review: "На перевірці", issued: "Видано", void: "Анульовано" };
const EVENT_LABELS = { created: "Створено", report_updated: "Дані чернетки оновлено", status_changed: "Статус змінено" };
const DRAFT_FIELDS = ["input", "select", "textarea"];

function setStatus(node, message, isError = false) {
  node.hidden = !message;
  node.textContent = message;
  node.classList.toggle("is-error", isError);
}

function formatDate(value) {
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function reportIdFromUrl() {
  return new URLSearchParams(window.location.search).get("id")?.trim() || "";
}

function setEditable(form, editable) {
  form.querySelectorAll(DRAFT_FIELDS.join(", ")).forEach((element) => { element.disabled = !editable; });
  form.querySelector("#detail-save").hidden = !editable;
  form.querySelector("#detail-cancel").hidden = !editable;
  form.querySelector("#detail-edit").hidden = editable;
}

function numberOrNull(value) {
  return value === "" ? null : Number(value);
}

function populateGradeSelect(select, mappings, category) {
  const selectedValue = select.value;
  select.replaceChildren(new Option("Не підтверджено", ""));
  mappings
    .filter((item) => item.category === category)
    .forEach((item) => select.add(new Option(item.grade_label, String(item.grade_value))));
  select.value = selectedValue;
}

function populateExpertGradeSelects(form, mappings) {
  populateGradeSelect(form.querySelector("#detail-expert-proportions"), mappings, "proportions");
  populateGradeSelect(form.querySelector("#detail-expert-cut"), mappings, "cut");
}

function payloadFromForm(form) {
  const data = new FormData(form);
  const numericStoneFields = [
    "carat_weight", "color_grade", "clarity_grade", "measurements_length", "measurements_width",
    "measurements_depth", "table_percent", "depth_percent", "crown_angle", "pavilion_angle",
    "polish_grade", "symmetry_grade", "fluorescence_grade",
  ];
  const stone = Object.fromEntries([...data.entries()].filter(([key]) => !["examination_date", "expert_comment", "expert_proportions_grade", "expert_cut_grade"].includes(key)));
  numericStoneFields.forEach((key) => { stone[key] = Number(stone[key]); });
  ["girdle_thickness", "culet_size", "identification_method", "identification_conclusion"].forEach((key) => { stone[key] = stone[key] || null; });
  return {
    examination_date: data.get("examination_date"),
    expert_comment: data.get("expert_comment") || null,
    expert_proportions_grade: numberOrNull(data.get("expert_proportions_grade")),
    expert_cut_grade: numberOrNull(data.get("expert_cut_grade")),
    stone,
  };
}

function populateForm(form, report) {
  const values = {
    ...report.stone,
    examination_date: report.examination_date || "",
    expert_comment: report.expert_comment || "",
    expert_proportions_grade: report.expert_proportions_grade ?? "",
    expert_cut_grade: report.expert_cut_grade ?? "",
  };
  for (const [name, value] of Object.entries(values)) {
    const field = form.elements.namedItem(name);
    if (field) field.value = value ?? "";
  }
}

function renderEvents(container, events) {
  container.replaceChildren();
  if (!events.length) {
    container.textContent = "Подій ще немає.";
    return;
  }
  for (const event of events) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = EVENT_LABELS[event.action] || event.action;
    const details = document.createElement("span");
    const transition = event.from_status || event.to_status
      ? ` · ${STATUS_LABELS[event.from_status] || event.from_status || "—"} → ${STATUS_LABELS[event.to_status] || event.to_status || "—"}`
      : "";
    details.textContent = `${formatDate(event.created_at)}${transition}${event.reason ? ` · ${event.reason}` : ""}`;
    item.append(title, details);
    container.append(item);
  }
}

function renderMedia(container, reportId, assets, token) {
  container.replaceChildren();
  if (!assets.length) {
    const item = document.createElement("li");
    item.textContent = "Приватних вкладень немає.";
    container.append(item);
    return;
  }
  for (const asset of assets) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = getReportMediaContentUrl(reportId, asset.media_id);
    link.textContent = asset.original_filename;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.addEventListener("click", (event) => {
      // Protected content requires the bearer token; the browser cannot attach it to a plain link.
      event.preventDefault();
      fetch(link.href, { headers: { Authorization: `Bearer ${token}` } })
        .then((response) => response.ok ? response.blob() : Promise.reject())
        .then((blob) => window.open(URL.createObjectURL(blob), "_blank", "noopener"));
    });
    item.append(link, document.createTextNode(` · ${asset.asset_type}`));
    container.append(item);
  }
}

function passportUrl(publicId) {
  const url = new URL("/passport.html", window.location.origin);
  url.searchParams.set("id", publicId);
  return url.toString();
}

async function renderPassportControls({ report, currentUser, token, onStatus }) {
  const section = document.getElementById("detail-passport");
  const state = document.getElementById("detail-passport-state");
  const link = document.getElementById("detail-passport-link");
  const qr = document.getElementById("detail-passport-qr");
  const publish = document.getElementById("detail-passport-publish");
  const reissue = document.getElementById("detail-passport-reissue");
  const revoke = document.getElementById("detail-passport-revoke");
  if (!section || currentUser.role !== "admin") return;
  section.hidden = false;
  [link, qr, publish, reissue, revoke].forEach((element) => { element.hidden = true; });
  if (report.status !== "issued") {
    state.textContent = "Публікація стане доступною після видачі звіту admin.";
    return;
  }
  try {
    const passport = await getReportPassport(report.report_id, token);
    const url = passportUrl(passport.public_id);
    state.textContent = "Паспорт опубліковано. Перевипуск одразу відкликає попереднє посилання.";
    link.href = url;
    link.hidden = false;
    reissue.hidden = false;
    revoke.hidden = false;
    const qrBlob = await getReportPassportQr(report.report_id, url, token);
    const previousUrl = qr.dataset.objectUrl;
    if (previousUrl) URL.revokeObjectURL(previousUrl);
    qr.dataset.objectUrl = URL.createObjectURL(qrBlob);
    qr.src = qr.dataset.objectUrl;
    qr.hidden = false;
  } catch (error) {
    if (!(error instanceof ApiRequestError) || error.status !== 404) {
      state.textContent = "Не вдалося завантажити стан публікації.";
      return;
    }
    state.textContent = "Паспорт ще не опубліковано.";
    publish.hidden = false;
  }
  publish.onclick = async () => {
    try {
      onStatus("Публікація паспорта…");
      await publishReportPassport(report.report_id, token);
      await renderPassportControls({ report, currentUser, token, onStatus });
      onStatus("Паспорт опубліковано.");
    } catch (error) { onStatus(error.message || "Не вдалося опублікувати паспорт.", true); }
  };
  reissue.onclick = async () => {
    if (!window.confirm("Перевипустити посилання? Попередній QR-код перестане працювати.")) return;
    try {
      onStatus("Перевипуск посилання…");
      await reissueReportPassport(report.report_id, token);
      await renderPassportControls({ report, currentUser, token, onStatus });
      onStatus("Нове публічне посилання створено.");
    } catch (error) { onStatus(error.message || "Не вдалося перевипустити посилання.", true); }
  };
  revoke.onclick = async () => {
    if (!window.confirm("Відкликати публічний паспорт? Посилання й QR одразу перестануть працювати.")) return;
    try {
      onStatus("Відкликання публікації…");
      await revokeReportPassport(report.report_id, token);
      await renderPassportControls({ report, currentUser, token, onStatus });
      onStatus("Публікацію паспорта відкликано.");
    } catch (error) { onStatus(error.message || "Не вдалося відкликати паспорт.", true); }
  };
}

function renderTransitionControls(container, helpNode, report, currentUser, onTransition) {
  container.replaceChildren();
  const isAdmin = currentUser.role === "admin";
  const isOwner = currentUser.expert_id === report.expert_id;
  const options = [];
  if (report.status === "draft" && (isOwner || isAdmin)) options.push(["review", "Передати на перевірку"]);
  if (report.status === "review" && isAdmin) {
    options.push(["draft", "Повернути в чернетку"], ["issued", "Видати звіт"], ["void", "Анулювати"]);
  }
  if (report.status === "issued" && isAdmin) options.push(["void", "Анулювати"]);
  for (const [targetStatus, label] of options) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = targetStatus === "issued" ? "btn btn-primary" : "btn btn-outline";
    button.textContent = label;
    button.disabled = targetStatus === "issued" && (report.expert_proportions_grade === null || report.expert_cut_grade === null);
    if (button.disabled) button.title = "Для видачі потрібні підтверджені експертом Proportions і Final Cut.";
    button.addEventListener("click", () => onTransition(targetStatus));
    container.append(button);
  }
  if (report.status === "review" && (report.expert_proportions_grade === null || report.expert_cut_grade === null)) {
    helpNode.textContent = "Для видачі поверніть звіт у чернетку та оберіть підтверджені експертом Proportions і Final Cut.";
  } else {
    helpNode.textContent = report.status === "draft"
      ? "Чернетку може редагувати її автор або admin."
      : "Після передачі на перевірку поля звіту заблоковані; переходи контролює сервер.";
  }
}

export async function initReportDetail() {
  const root = document.querySelector("[data-report-detail]");
  if (!root) return;
  const token = localStorage.getItem("token");
  const reportId = reportIdFromUrl();
  const form = document.getElementById("report-detail-form");
  const status = document.getElementById("report-detail-status");
  if (!token || !reportId || !form) {
    setStatus(status, "Не вказано номер звіту.", true);
    return;
  }
  let report;
  let currentUser;
  let gradeLabels = new Map();
  const refresh = async () => {
    try {
      const [freshReport, events, media] = await Promise.all([
        getDomainReport(reportId, token), getReportEvents(reportId, token), getReportMedia(reportId, token),
      ]);
      report = freshReport;
      populateForm(form, report);
      document.getElementById("report-detail-title").textContent = report.report_id;
      document.getElementById("report-detail-subtitle").textContent = `Створено: ${formatDate(report.created_at || report.report_date)}`;
      const badge = document.getElementById("detail-status-badge");
      badge.textContent = STATUS_LABELS[report.status] || report.status;
      badge.dataset.status = report.status;
      document.getElementById("detail-system-summary").textContent = `Системний IDC: Proportions ${report.system_proportions_grade ?? "—"}, Final Cut ${report.system_cut_grade ?? "—"}.`;
      const confirmedProportions = report.expert_proportions_grade === null
        ? "не задано"
        : gradeLabels.get(`proportions:${report.expert_proportions_grade}`) || String(report.expert_proportions_grade);
      const confirmedCut = report.expert_cut_grade === null
        ? "не задано"
        : gradeLabels.get(`cut:${report.expert_cut_grade}`) || String(report.expert_cut_grade);
      document.getElementById("detail-expert-summary").textContent = `Експертне підтвердження: Proportions ${confirmedProportions}, Final Cut ${confirmedCut}.`;
      renderEvents(document.getElementById("detail-events"), events);
      renderMedia(document.getElementById("detail-media"), reportId, media, token);
      await renderPassportControls({ report, currentUser, token, onStatus: (message, isError) => setStatus(status, message, isError) });
      renderTransitionControls(document.getElementById("detail-transitions"), document.getElementById("detail-transition-help"), report, currentUser, async (targetStatus) => {
        try {
          setStatus(status, "Зміна статусу…");
          const reason = document.getElementById("detail-transition-reason").value.trim();
          await transitionDomainReport(reportId, { target_status: targetStatus, reason: reason || null }, token);
          setStatus(status, "Статус звіту оновлено.");
          await refresh();
        } catch (error) { setStatus(status, error.message || "Не вдалося змінити статус.", true); }
      });
      const canEdit = report.status === "draft" && (currentUser.role === "admin" || currentUser.expert_id === report.expert_id);
      setEditable(form, false);
      form.querySelector("#detail-edit").hidden = !canEdit;
      if (new URLSearchParams(window.location.search).get("edit") === "1" && canEdit) setEditable(form, true);
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) { logout("/login.html"); return; }
      setStatus(status, error.status === 403 ? "У вас немає доступу до цього звіту." : "Не вдалося завантажити приватний звіт.", true);
    }
  };
  try {
    const [user, mappings] = await Promise.all([getCurrentUser(token), getGradeMappings()]);
    currentUser = user;
    gradeLabels = new Map(mappings.map((item) => [`${item.category}:${item.grade_value}`, item.grade_label]));
    populateExpertGradeSelects(form, mappings);
  } catch { logout("/login.html"); return; }
  form.querySelector("#detail-edit").addEventListener("click", () => setEditable(form, true));
  form.querySelector("#detail-cancel").addEventListener("click", () => { populateForm(form, report); setEditable(form, false); });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    try {
      setStatus(status, "Збереження змін…");
      await updateDomainReport(reportId, payloadFromForm(form), token);
      setStatus(status, "Зміни чернетки збережено.");
      await refresh();
    } catch (error) { setStatus(status, error.message || "Не вдалося зберегти зміни.", true); }
  });
  await refresh();
}
