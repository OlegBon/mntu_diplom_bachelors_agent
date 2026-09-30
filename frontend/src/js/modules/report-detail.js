import {
  ApiRequestError,
  getCurrentUser,
  getDomainReport,
  getGradeMappings,
  getReferenceValues,
  getReportEvents,
  getReportNarrativeQuality,
  getReportMedia,
  getReportMediaContentUrl,
  updateReportMediaPublication,
  getReportValuations,
  getReportPassport,
  getReportPassportPdf,
  getReportPassportQr,
  publishReportPassport,
  reissueReportPassport,
  revokeReportPassport,
  transitionDomainReport,
  updateDomainReport,
} from "./api.js";
import { isConfirmedUnauthorized, logout } from "./auth.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";
import { createDraftWorkSessionTracker } from "./report-work-session.js";
import { formatCurrency, formatDate as formatLocalizedDate, formatNumber, t } from "./i18n.js";

const STATUS_LABELS = { draft: "dashboard.statusDraft", review: "dashboard.statusReview", issued: "dashboard.statusIssued", void: "dashboard.statusVoid" };
const MEDIA_TYPE_LABELS = {
  stone_photo: "detail.stonePhoto",
  plotting_diagram: "detail.plottingDiagram",
};
const EVENT_LABELS = {
  created: "detail.eventCreated", report_updated: "detail.eventUpdated", status_changed: "detail.eventStatusChanged",
  passport_published: "detail.eventPassportPublished", passport_reissued: "detail.eventPassportReissued", passport_revoked: "detail.eventPassportRevoked",
  media_published: "detail.eventMediaPublished", media_unpublished: "detail.eventMediaUnpublished",
  system_market_reference_added: "detail.eventSystemReference", market_reference_added: "detail.eventAdminReference", legacy_import: "detail.eventLegacyImport",
};
const DRAFT_FIELDS = ["input", "select", "textarea"];

function setStatus(node, message, isError = false) {
  node.hidden = !message;
  node.textContent = message;
  node.classList.toggle("is-error", isError);
}

function formatDate(value) {
  return formatLocalizedDate(new Date(value), { dateStyle: "medium", timeStyle: "short" });
}

function formatAmount(amount, currencyCode) {
  return formatCurrency(Number(amount), currencyCode, { minimumFractionDigits: 2 });
}

function formatFxRate(value) {
  if (value === null || value === undefined) return "—";
  return formatNumber(Number(value), { maximumFractionDigits: 8 });
}

function reportIdFromUrl() {
  return new URLSearchParams(window.location.search).get("id")?.trim() || "";
}

function setEditable(form, editable) {
  form.querySelectorAll(DRAFT_FIELDS.join(", ")).forEach((element) => {
    if (element.id !== "detail-expert-cut-result") element.disabled = !editable;
  });
  form.querySelector("#detail-save").hidden = !editable;
  form.querySelector("#detail-cancel").hidden = !editable;
  form.querySelector("#detail-edit").hidden = editable;
}

function numberOrNull(value) {
  return value === "" ? null : Number(value);
}

function populateGradeSelect(select, mappings, category, emptyLabel = t("detail.notConfirmed")) {
  const selectedValue = select.value;
  select.replaceChildren(new Option(emptyLabel, ""));
  mappings
    .filter((item) => item.category === category)
    .forEach((item) => select.add(new Option(item.grade_label, String(item.grade_value))));
  select.value = selectedValue;
}

function populateExpertGradeSelects(form, mappings) {
  populateGradeSelect(form.querySelector("#detail-color"), mappings, "color", t("detail.chooseColor"));
  populateGradeSelect(form.querySelector("#detail-clarity"), mappings, "clarity", t("detail.chooseClarity"));
  populateGradeSelect(form.querySelector("#detail-fluorescence"), mappings, "fluorescence", t("detail.chooseValue"));
  populateGradeSelect(form.querySelector("#detail-polish"), mappings, "polish", t("detail.chooseGrade"));
  populateGradeSelect(form.querySelector("#detail-symmetry"), mappings, "symmetry", t("detail.chooseGrade"));
  populateGradeSelect(form.querySelector("#detail-expert-proportions"), mappings, "proportions", t("detail.notSpecified"));
}

function populateReferenceSelect(select, references, category) {
  const selectedValue = select.value;
  select.replaceChildren(new Option(t("detail.notSpecified"), ""));
  references
    .filter((entry) => entry.category === category)
    .forEach((entry) => select.add(new Option(entry.label, entry.code)));
  select.value = selectedValue;
}

function updateDerivedExpertCut(form, gradeLabels) {
  const target = form.querySelector("#detail-expert-cut-result");
  const values = ["expert_proportions_grade", "polish_grade", "symmetry_grade"]
    .map((name) => form.elements.namedItem(name)?.value ?? "");
  if (!target || values.some((value) => value === "")) {
    if (target) target.value = "—";
    return;
  }
  const grades = values.map(Number);
  if (grades.some((grade) => !Number.isInteger(grade) || grade < 0)) {
    target.value = "—";
    return;
  }
  const cut = Math.max(...grades);
  target.value = gradeLabels.get(`cut:${cut}`) || String(cut);
}

function payloadFromForm(form) {
  const data = new FormData(form);
  const numericStoneFields = [
    "carat_weight", "color_grade", "clarity_grade", "measurements_length", "measurements_width",
    "measurements_depth", "table_percent", "depth_percent", "crown_angle", "pavilion_angle",
    "polish_grade", "symmetry_grade", "fluorescence_grade",
  ];
  const stone = Object.fromEntries([...data.entries()].filter(([key]) => !["examination_date", "expert_comment", "expert_proportions_grade"].includes(key)));
  numericStoneFields.forEach((key) => { stone[key] = Number(stone[key]); });
  ["girdle_thickness", "culet_size", "identification_method", "identification_conclusion"].forEach((key) => { stone[key] = stone[key] || null; });
  return {
    examination_date: data.get("examination_date"),
    expert_comment: data.get("expert_comment") || null,
    expert_proportions_grade: numberOrNull(data.get("expert_proportions_grade")),
    stone,
  };
}

function populateForm(form, report, gradeLabels) {
  const values = {
    ...report.stone,
    examination_date: report.examination_date || "",
    expert_comment: report.expert_comment || "",
    expert_proportions_grade: report.expert_proportions_grade ?? "",
  };
  for (const [name, value] of Object.entries(values)) {
    const field = form.elements.namedItem(name);
    if (field) field.value = value ?? "";
  }
  const derivedCut = document.getElementById("detail-expert-cut-result");
  if (derivedCut) {
    derivedCut.value = report.expert_cut_grade === null
      ? "—"
      : gradeLabels.get(`cut:${report.expert_cut_grade}`) || String(report.expert_cut_grade);
  }
}

function renderEvents(container, events) {
  container.replaceChildren();
  if (!events.length) {
    container.textContent = t("detail.noEvents");
    return;
  }
  for (const event of events) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = EVENT_LABELS[event.action] ? t(EVENT_LABELS[event.action]) : event.action;
    const details = document.createElement("span");
    const transition = event.from_status || event.to_status
      ? ` · ${STATUS_LABELS[event.from_status] ? t(STATUS_LABELS[event.from_status]) : event.from_status || "—"} → ${STATUS_LABELS[event.to_status] ? t(STATUS_LABELS[event.to_status]) : event.to_status || "—"}`
      : "";
    const reason = ["media_published", "media_unpublished"].includes(event.action) && event.reason
      ? event.reason.replace(/^(stone_photo|plotting_diagram)(?= · |$)/, (assetType) => t(MEDIA_TYPE_LABELS[assetType]))
      : event.reason;
    details.textContent = `${formatDate(event.created_at)}${transition}${reason ? ` · ${reason}` : ""}`;
    item.append(title, details);
    container.append(item);
  }
}

function renderNarrativeQuality(container, snapshot) {
  container.replaceChildren();
  if (!snapshot.warnings.length) {
    container.append(document.createTextNode("Пояснюваних сигналів заповнення зараз немає."));
    return;
  }
  snapshot.warnings.forEach((warning) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = `${warning.label}: `;
    item.append(title, document.createTextNode(warning.message));
    container.append(item);
  });
}

function renderMedia(container, report, assets, currentUser, token, onRequestPublication) {
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
    link.href = getReportMediaContentUrl(report.report_id, asset.media_id);
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
    item.append(link, document.createTextNode(` · ${MEDIA_TYPE_LABELS[asset.asset_type] ? t(MEDIA_TYPE_LABELS[asset.asset_type]) : t("detail.attachment")}`));
    const canManagePublication = currentUser.role === "admin"
      && report.status === "issued"
      && ["stone_photo", "plotting_diagram"].includes(asset.asset_type)
      && ["image/jpeg", "image/png", "image/webp"].includes(asset.mime_type);
    if (canManagePublication) {
      const publication = document.createElement("button");
      publication.type = "button";
      publication.className = "btn btn-outline btn--compact";
      publication.textContent = asset.is_public ? t("detail.removeFromPassport") : t("detail.publishInPassport");
      publication.addEventListener("click", () => onRequestPublication(asset, !asset.is_public, publication));
      item.append(document.createTextNode(" "), publication);
    } else if (asset.is_public) {
      item.append(document.createTextNode(` · ${t("detail.publishedInPassport")}`));
    }
    container.append(item);
  }
}

function renderValuations(container, helpNode, valuations) {
  container.replaceChildren();
  const marketReferences = valuations.filter((valuation) => ["market_reference", "system_market_reference"].includes(valuation.valuation_kind));
  if (!marketReferences.length) {
    const item = document.createElement("li");
    item.textContent = "Системного або підтвердженого ринкового орієнтира ще немає.";
    container.append(item);
    return;
  }
  helpNode.textContent = "Кожен орієнтир належить окремому провайдеру та знімку. Системний орієнтир формується автоматично з останнього затвердженого знімка; підтверджений орієнтир окремо перевіряє адміністратор. Орієнтири не є експертною, продажною чи транзакційною ціною.";
  if (marketReferences.length > 1) {
    helpNode.append(document.createTextNode(" Поточний запис відкритий; попередні збережені орієнтири згорнуті."));
  }
  for (const [index, valuation] of marketReferences.entries()) {
    const isSystemReference = valuation.valuation_kind === "system_market_reference";
    const item = document.createElement("li");
    item.className = "market-reference-card";
    const disclosure = document.createElement("details");
    disclosure.className = "market-reference-card__disclosure";
    disclosure.open = index === 0;
    const summary = document.createElement("summary");
    summary.className = "market-reference-card__summary";
    const amount = document.createElement("strong");
    amount.textContent = formatAmount(valuation.amount, valuation.currency_code);
    const label = document.createElement("span");
    label.textContent = isSystemReference ? "Системний довідковий орієнтир" : "Підтверджений довідковий орієнтир";
    summary.append(amount, label);
    const details = document.createElement("dl");
    details.className = "market-reference-card__details";
    const addDetail = (term, value) => {
      const row = document.createElement("div");
      const dt = document.createElement("dt"); dt.textContent = term;
      const dd = document.createElement("dd"); dd.textContent = value;
      row.append(dt, dd); details.append(row);
    };
    addDetail("Провайдер", valuation.source_name);
    addDetail("Знімок провайдера", `#${valuation.market_snapshot_id ?? "—"}`);
    addDetail("Отримано", formatDate(valuation.observed_at));
    if (valuation.converted_amount && valuation.converted_currency_code) {
      const rateDate = valuation.fx_rate_date ? new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(`${valuation.fx_rate_date}T12:00:00`)) : "—";
      addDetail("Еквівалент", formatAmount(valuation.converted_amount, valuation.converted_currency_code));
      addDetail("Курс НБУ", `${formatFxRate(valuation.fx_rate)} UAH/USD · ${rateDate} · знімок #${valuation.fx_snapshot_id ?? "—"}`);
    }
    disclosure.append(summary, details);
    if (valuation.applicability_note) {
      const note = document.createElement("p");
      note.className = "market-reference-card__note";
      note.append(document.createTextNode("Підтвердження: "), document.createTextNode(valuation.applicability_note));
      disclosure.append(note);
    } else if (isSystemReference) {
      const note = document.createElement("p");
      note.className = "market-reference-card__note";
      note.textContent = `Автоматично розраховано за останнім затвердженим знімком ${valuation.source_name}; застосовність не підтверджена адміністратором.`;
      disclosure.append(note);
    }
    item.append(disclosure);
    container.append(item);
  }
}

function passportUrl(publicId) {
  const url = new URL("/passport.html", window.location.origin);
  url.searchParams.set("id", publicId);
  return url.toString();
}

async function copyText(value) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const helper = document.createElement("textarea");
  helper.value = value;
  helper.setAttribute("readonly", "");
  helper.style.position = "fixed";
  helper.style.opacity = "0";
  document.body.append(helper);
  helper.select();
  const copied = document.execCommand("copy");
  helper.remove();
  if (!copied) throw new Error("Не вдалося скопіювати дані");
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function renderPassportControls({ report, currentUser, token, onStatus }) {
  const section = document.getElementById("detail-passport");
  const state = document.getElementById("detail-passport-state");
  const code = document.getElementById("detail-passport-code");
  const link = document.getElementById("detail-passport-link");
  const qr = document.getElementById("detail-passport-qr");
  const publish = document.getElementById("detail-passport-publish");
  const copyLink = document.getElementById("detail-passport-copy-link");
  const copyCode = document.getElementById("detail-passport-copy-code");
  const pdf = document.getElementById("detail-passport-pdf");
  const reissue = document.getElementById("detail-passport-reissue");
  const revoke = document.getElementById("detail-passport-revoke");
  if (!section || currentUser.role !== "admin") return;
  section.hidden = false;
  [code, link, qr, publish, copyLink, copyCode, pdf, reissue, revoke].forEach((element) => { element.hidden = true; });
  publish.disabled = false;
  publish.textContent = t("detail.publishPassport");
  if (report.status !== "issued") {
    state.textContent = t("detail.passportIssuedOnly");
    return;
  }
  publish.onclick = async () => {
    if (publish.dataset.submitting === "true") return;
    publish.dataset.submitting = "true";
    publish.disabled = true;
    publish.textContent = t("detail.publishing");
    try {
      onStatus(t("detail.publishingPassport"));
      await publishReportPassport(report.report_id, token);
      await renderPassportControls({ report, currentUser, token, onStatus });
      onStatus(t("detail.passportPublished"));
    } catch (error) {
      onStatus(error.message || t("detail.publishPassportFailed"), true);
      publish.disabled = false;
      publish.textContent = t("detail.publishPassport");
    } finally {
      delete publish.dataset.submitting;
    }
  };
  try {
    const { passport } = await getReportPassport(report.report_id, token);
    if (!passport) {
      state.textContent = t("detail.passportNotPublished");
      publish.hidden = false;
      return;
    }
    const url = passportUrl(passport.public_id);
    state.textContent = "Паспорт опубліковано. Його можна перевірити за посиланням, QR або кодом; перевипуск одразу відкликає попередні дані доступу.";
    code.querySelector("code").textContent = passport.public_id;
    code.hidden = false;
    link.href = url;
    link.hidden = false;
    copyLink.hidden = false;
    copyCode.hidden = false;
    pdf.hidden = false;
    reissue.hidden = false;
    revoke.hidden = false;
    const qrBlob = await getReportPassportQr(report.report_id, url, token);
    const previousUrl = qr.dataset.objectUrl;
    if (previousUrl) URL.revokeObjectURL(previousUrl);
    qr.dataset.objectUrl = URL.createObjectURL(qrBlob);
    qr.src = qr.dataset.objectUrl;
    qr.hidden = false;
    copyLink.onclick = async () => {
      try { await copyText(url); onStatus(t("detail.publicLinkCopied")); }
      catch (error) { onStatus(error.message || t("detail.copyLinkFailed"), true); }
    };
    copyCode.onclick = async () => {
      try { await copyText(passport.public_id); onStatus(t("detail.passportCodeCopied")); }
      catch (error) { onStatus(error.message || t("detail.copyCodeFailed"), true); }
    };
    pdf.onclick = async () => {
      try {
        onStatus(t("detail.generatingPassportPdf"));
        const document = await getReportPassportPdf(report.report_id, url, token);
        downloadBlob(document, `passport-${report.report_id}.pdf`);
        onStatus(t("detail.passportPdfDownloaded"));
      } catch (error) { onStatus(error.message || t("detail.passportPdfFailed"), true); }
    };
  } catch {
    state.textContent = "Не вдалося завантажити стан публікації.";
    return;
  }
  reissue.onclick = async () => {
    if (!window.confirm(t("detail.reissueConfirm"))) return;
    try {
      onStatus(t("detail.reissuingPassport"));
      await reissueReportPassport(report.report_id, token);
      await renderPassportControls({ report, currentUser, token, onStatus });
      onStatus(t("detail.passportReissued"));
    } catch (error) { onStatus(error.message || t("detail.reissueFailed"), true); }
  };
  revoke.onclick = async () => {
    if (!window.confirm(t("detail.revokeConfirm"))) return;
    try {
      onStatus(t("detail.revokingPassport"));
      await revokeReportPassport(report.report_id, token);
      await renderPassportControls({ report, currentUser, token, onStatus });
      onStatus(t("detail.passportRevoked"));
    } catch (error) { onStatus(error.message || t("detail.revokeFailed"), true); }
  };
}

function renderTransitionControls(container, helpNode, report, currentUser, onTransition) {
  container.replaceChildren();
  const isAdmin = currentUser.role === "admin";
  const isOwner = currentUser.expert_id === report.expert_id;
  const options = [];
  if (report.status === "draft" && (isOwner || isAdmin)) options.push(["review", t("detail.sendForReview")]);
  if (report.status === "review" && isAdmin) {
    options.push(["draft", t("detail.returnToDraft")], ["issued", t("detail.issueReport")], ["void", t("detail.voidReport")]);
  }
  if (report.status === "issued" && isAdmin) options.push(["void", t("detail.voidReport")]);
  for (const [targetStatus, label] of options) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = targetStatus === "issued" ? "btn btn-primary" : "btn btn-outline";
    button.textContent = label;
    button.disabled = targetStatus === "issued" && report.expert_proportions_grade === null;
    if (button.disabled) button.title = t("detail.issueNeedsProportions");
    button.addEventListener("click", () => onTransition(targetStatus));
    container.append(button);
  }
  if (report.status === "review" && report.expert_proportions_grade === null) {
    helpNode.textContent = t("detail.reviewNeedsProportions");
  } else {
    helpNode.textContent = report.status === "draft"
      ? t("detail.draftEditHelp")
      : t("detail.lockedAfterReview");
  }
}

export async function initReportDetail() {
  const root = document.querySelector("[data-report-detail]");
  if (!root) return;
  const token = localStorage.getItem("token");
  const reportId = reportIdFromUrl();
  const form = document.getElementById("report-detail-form");
  const status = document.getElementById("report-detail-status");
  const mediaPublicationDialog = document.getElementById("media-publication-dialog");
  const mediaPublicationForm = document.getElementById("media-publication-form");
  const mediaPublicationDescription = document.getElementById("media-publication-description");
  const mediaPublicationStatus = document.getElementById("media-publication-status");
  const mediaPublicationSubmit = document.getElementById("media-publication-submit");
  if (!token || !reportId || !form) {
    setStatus(status, "Не вказано номер звіту.", true);
    return;
  }
  let report;
  let currentUser;
  let gradeLabels = new Map();
  let printStarted = false;
  let workSessionTracker;
  let pendingMediaPublication;
  let mediaPublicationTrigger;
  let isEditing = new URLSearchParams(window.location.search).get("edit") === "1";
  const closeMediaPublicationDialog = () => {
    pendingMediaPublication = undefined;
    mediaPublicationStatus.hidden = true;
    mediaPublicationStatus.textContent = "";
    if (mediaPublicationDialog.open) mediaPublicationDialog.close();
  };
  const openMediaPublicationDialog = (asset, isPublic, trigger) => {
    pendingMediaPublication = { asset, isPublic };
    mediaPublicationTrigger = trigger;
    mediaPublicationDescription.textContent = isPublic
      ? "Зображення стане доступним у публічному паспорті лише за чинним посиланням або QR-кодом. Воно не потрапляє до PDF."
      : "Зображення перестане відображатися у публічному паспорті. Приватне вкладення у звіті буде збережено.";
    mediaPublicationSubmit.textContent = isPublic ? "Опублікувати в паспорті" : "Прибрати з паспорта";
    mediaPublicationStatus.hidden = true;
    mediaPublicationDialog.showModal();
  };
  const refresh = async () => {
    try {
      const [freshReport, events, media, narrativeQuality] = await Promise.all([
        getDomainReport(reportId, token), getReportEvents(reportId, token), getReportMedia(reportId, token),
        getReportNarrativeQuality(reportId, token).catch(() => null),
      ]);
      report = freshReport;
      populateForm(form, report, gradeLabels);
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
      document.getElementById("detail-expert-summary").textContent = `Експертні grades: Proportions ${confirmedProportions}, підсумковий Cut ${confirmedCut}.`;
      renderEvents(document.getElementById("detail-events"), events);
      const narrativeNode = document.getElementById("detail-narrative-quality");
      if (narrativeQuality) renderNarrativeQuality(narrativeNode, narrativeQuality);
      else narrativeNode.textContent = "Текстові метадані тимчасово недоступні.";
      renderMedia(
        document.getElementById("detail-media"), report, media, currentUser, token, openMediaPublicationDialog,
      );
      try {
        const valuations = await getReportValuations(reportId, token);
        renderValuations(document.getElementById("detail-valuations"), document.getElementById("detail-valuations-help"), valuations);
      } catch {
        document.getElementById("detail-valuations").textContent = "Не вдалося завантажити ринковий орієнтир.";
      }
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
      const canTrack = report.status === "draft" && currentUser.role === "gemologist" && currentUser.expert_id === report.expert_id;
      setEditable(form, isEditing && canEdit);
      form.querySelector("#detail-edit").hidden = !canEdit;
      workSessionTracker?.setEnabled(canTrack && !form.querySelector("#detail-save").hidden, { pauseOnDisable: report.status === "draft" });
      if (new URLSearchParams(window.location.search).get("print") === "1" && !printStarted) {
        printStarted = true;
        window.setTimeout(() => window.print(), 0);
      }
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) { logout("/login.html"); return; }
      setStatus(status, error.status === 403 ? "У вас немає доступу до цього звіту." : "Не вдалося завантажити приватний звіт.", true);
    }
  };
  try {
    const [user, mappings, references] = await Promise.all([getCurrentUser(token), getGradeMappings(), getReferenceValues(token)]);
    currentUser = user;
    gradeLabels = new Map(mappings.map((item) => [`${item.category}:${item.grade_value}`, item.grade_label]));
    populateExpertGradeSelects(form, mappings);
    populateReferenceSelect(form.querySelector("#detail-girdle"), references, "girdle_thickness");
    populateReferenceSelect(form.querySelector("#detail-culet"), references, "culet_size");
  } catch (error) {
    if (isConfirmedUnauthorized(error)) {
      logout("/login.html");
      return;
    }
    setStatus(status, "Не вдалося підготувати сторінку звіту. Сеанс збережено — оновіть сторінку після відновлення API.", true);
    return;
  }
  workSessionTracker = createDraftWorkSessionTracker({ reportId, token, form });
  document.getElementById("media-publication-dialog-close").addEventListener("click", closeMediaPublicationDialog);
  document.getElementById("media-publication-cancel").addEventListener("click", closeMediaPublicationDialog);
  mediaPublicationDialog.addEventListener("close", () => {
    pendingMediaPublication = undefined;
    mediaPublicationStatus.hidden = true;
    mediaPublicationStatus.textContent = "";
    if (document.activeElement === document.body) mediaPublicationTrigger?.focus();
    mediaPublicationTrigger = undefined;
  });
  mediaPublicationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!pendingMediaPublication) return;
    mediaPublicationSubmit.disabled = true;
    try {
      await updateReportMediaPublication(
        report.report_id, pendingMediaPublication.asset.media_id, pendingMediaPublication.isPublic, token,
      );
      const message = pendingMediaPublication.isPublic
        ? "Вкладення опубліковано в паспорті."
        : "Вкладення прибрано з паспорта.";
      closeMediaPublicationDialog();
      setStatus(status, message);
      await refresh();
    } catch (error) {
      setStatus(mediaPublicationStatus, error.message || "Не вдалося змінити видимість вкладення.", true);
    } finally {
      mediaPublicationSubmit.disabled = false;
    }
  });
  form.querySelector("#detail-edit").addEventListener("click", () => {
    isEditing = true;
    setEditable(form, true);
    workSessionTracker.setEnabled(currentUser.role === "gemologist" && currentUser.expert_id === report.expert_id);
  });
  form.querySelector("#detail-cancel").addEventListener("click", () => {
    isEditing = false;
    populateForm(form, report, gradeLabels);
    setEditable(form, false);
    workSessionTracker.setEnabled(false);
  });
  ["expert_proportions_grade", "polish_grade", "symmetry_grade"].forEach((name) => {
    form.elements.namedItem(name)?.addEventListener("change", () => updateDerivedExpertCut(form, gradeLabels));
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    try {
      setStatus(status, "Збереження змін…");
      await workSessionTracker.checkpointSave();
      await updateDomainReport(reportId, payloadFromForm(form), token);
      isEditing = false;
      setStatus(status, "Зміни чернетки збережено.");
      await refresh();
    } catch (error) { setStatus(status, error.message || "Не вдалося зберегти зміни.", true); }
  });
  await refresh();
  registerVisibleDataRefresh(refresh, { canRefresh: () => form.querySelector("#detail-save").hidden });
}
