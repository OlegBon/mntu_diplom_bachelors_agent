import { ApiRequestError, getGradeMappings, getPublicPassport } from "./api.js";

const ORIGIN_LABELS = {
  natural: "Природний",
  lab_grown: "Лабораторно вирощений",
  unknown: "Не визначено",
  other: "Інше",
};
const TREATMENT_LABELS = {
  not_assessed: "Не оцінено",
  none_detected: "Не виявлено",
  disclosed: "Заявлено",
  confirmed: "Підтверджено",
};
const IDENTIFICATION_LABELS = {
  preliminary: "Попередній",
  confirmed: "Підтверджено",
  inconclusive: "Невизначено",
};

function setStatus(node, message, isError = false) {
  node.hidden = !message;
  node.textContent = message;
  node.classList.toggle("is-error", isError);
}

function publicIdFromUrl() {
  return new URLSearchParams(window.location.search).get("id")?.trim() || "";
}

function setText(id, value) {
  document.getElementById(id).textContent = value ?? "—";
}

function formatDate(value) {
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "long" }).format(new Date(value));
}

function labelFor(labels, category, value) {
  return labels.get(`${category}:${value}`) || String(value ?? "—");
}

function renderPassport(passport, labels) {
  setText("passport-report-id", passport.report_id);
  setText("passport-issued-at", formatDate(passport.issued_at));
  setText("passport-shape", passport.shape);
  setText("passport-carat", `${passport.carat_weight} ct`);
  setText("passport-color", labelFor(labels, "color", passport.color_grade));
  setText("passport-clarity", labelFor(labels, "clarity", passport.clarity_grade));
  const dimensions = [passport.measurements_length, passport.measurements_width, passport.measurements_depth]
    .map((value) => value ?? "—")
    .join(" × ");
  setText("passport-dimensions", `${dimensions} mm`);
  setText("passport-system-proportions", labelFor(labels, "proportions", passport.system_proportions_grade));
  setText("passport-system-cut", labelFor(labels, "cut", passport.system_cut_grade));
  setText("passport-expert-proportions", labelFor(labels, "proportions", passport.expert_proportions_grade));
  setText("passport-expert-cut", labelFor(labels, "cut", passport.expert_cut_grade));
  setText("passport-origin", ORIGIN_LABELS[passport.origin] || passport.origin);
  setText("passport-treatment", TREATMENT_LABELS[passport.treatment_status] || passport.treatment_status);
  setText("passport-identification", IDENTIFICATION_LABELS[passport.identification_status] || passport.identification_status);
}

export async function initPublicPassport() {
  const root = document.querySelector("[data-public-passport]");
  if (!root) return;
  const status = document.getElementById("public-passport-status");
  const card = document.getElementById("public-passport-card");
  const publicId = publicIdFromUrl();
  if (!publicId) {
    setStatus(status, "Відкрийте паспорт за прямим посиланням або посиланням із QR-коду. Код зі сторінки звіту вводиться на головній.", true);
    return;
  }
  try {
    const [passport, mappings] = await Promise.all([getPublicPassport(publicId), getGradeMappings()]);
    const labels = new Map(mappings.map((item) => [`${item.category}:${item.grade_value}`, item.grade_label]));
    renderPassport(passport, labels);
    document.getElementById("public-passport-title").textContent = `Паспорт ${passport.report_id}`;
    document.getElementById("public-passport-subtitle").textContent = "Публічна проєкція виданого звіту.";
    card.hidden = false;
  } catch (error) {
    const message = error instanceof ApiRequestError && error.status === 404
      ? "Паспорт не знайдено або його публікацію відкликано."
      : "Не вдалося завантажити публічний паспорт. Спробуйте пізніше.";
    setStatus(status, message, true);
  }
}
