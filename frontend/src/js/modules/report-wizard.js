import {
  createDomainReport,
  getCurrentUser,
  getGradeMappings,
  getNextReportId,
  getReferenceValues,
  previewReportCalculation,
  uploadReportMedia,
} from "./api.js";
import { createWizardDraftStorage } from "./wizard-draft-storage.js";
import { createWizardWorkSessionTracker } from "./wizard-work-session.js";

const requiredPreviewNames = ["table_percent", "depth_percent", "crown_angle", "pavilion_angle", "polish_grade", "symmetry_grade"];
const implicitSubmitInputTypes = new Set(["date", "email", "number", "password", "search", "tel", "text", "url"]);

function setStatus(element, message, isError = false) {
  element.hidden = !message;
  element.textContent = message;
  element.classList.toggle("is-error", isError);
}

function setOptions(select, entries, valueKey, labelKey, includeBlank = false) {
  select.replaceChildren();
  if (includeBlank) select.add(new Option("Не зазначено", ""));
  entries.forEach((entry) => select.add(new Option(entry[labelKey], String(entry[valueKey]))));
  select.disabled = false;
}

function number(formData, name) {
  return Number(formData.get(name));
}

function stoneFromForm(formData) {
  return {
    shape: formData.get("shape"), carat_weight: number(formData, "carat_weight"),
    color_grade: number(formData, "color_grade"), clarity_grade: number(formData, "clarity_grade"),
    measurements_length: number(formData, "measurements_length"), measurements_width: number(formData, "measurements_width"),
    measurements_depth: number(formData, "measurements_depth"), table_percent: number(formData, "table_percent"),
    depth_percent: number(formData, "depth_percent"), crown_angle: number(formData, "crown_angle"),
    pavilion_angle: number(formData, "pavilion_angle"), girdle_thickness: formData.get("girdle_thickness") || null,
    culet_size: formData.get("culet_size") || null, polish_grade: number(formData, "polish_grade"),
    symmetry_grade: number(formData, "symmetry_grade"), fluorescence_grade: number(formData, "fluorescence_grade"),
    origin: formData.get("origin"), treatment_status: formData.get("treatment_status"),
    identification_status: formData.get("identification_status"), identification_method: formData.get("identification_method") || null,
    identification_conclusion: formData.get("identification_conclusion") || null, market_status: "not_for_sale",
  };
}

function calculationInput(formData) {
  return {
    ...Object.fromEntries(requiredPreviewNames.map((name) => [name, number(formData, name)])),
    carat_weight: formData.get("carat_weight") === "" ? null : String(formData.get("carat_weight")),
    color_grade: formData.get("color_grade") === "" ? null : number(formData, "color_grade"),
    clarity_grade: formData.get("clarity_grade") === "" ? null : number(formData, "clarity_grade"),
    shape: formData.get("shape") || null,
    origin: formData.get("origin") || null,
  };
}

export async function initReportWizard() {
  const form = document.getElementById("wizard-form");
  if (!form) return;
  const token = localStorage.getItem("token");
  const status = document.getElementById("wizard-status");
  const tabs = [...document.querySelectorAll(".stepper-tabs .tab")];
  const steps = [...document.querySelectorAll(".step-content")];
  const next = document.getElementById("next-btn");
  const previous = document.getElementById("prev-btn");
  const save = document.getElementById("save-btn");
  const clearDraftButton = document.getElementById("clear-wizard-draft");
  const restoreDialog = document.getElementById("wizard-restore-dialog");
  const clearDialog = document.getElementById("wizard-clear-dialog");
  let draftStorage = null;
  let hasUnsavedDraft = false;
  let suppressDraftPersistence = false;
  let workSessionTracker = null;
  let schedulePreview = () => {};
  const updateClearDraftButton = () => { clearDraftButton.hidden = !hasUnsavedDraft; };
  const persistDraft = () => {
    if (!draftStorage || suppressDraftPersistence) return;
    hasUnsavedDraft = draftStorage.save(form, currentStep);
    updateClearDraftButton();
  };
  let gradeLabels = new Map();
  const renderInitialFinish = () => {
    ["polish", "symmetry"].forEach((category) => {
      const select = document.querySelector(`[data-grade-category="${category}"]`);
      const target = document.getElementById(category === "polish" ? "res-pol" : "res-sym");
      target.textContent = gradeLabels.get(`${category}:${select.value}`) || "--";
      target.classList.toggle("placeholder", target.textContent === "--");
    });
  };
  let currentStep = 1;
  const updateStep = () => {
    steps.forEach((step) => { const active = Number(step.dataset.step) === currentStep; step.classList.toggle("active", active); step.hidden = !active; });
    tabs.forEach((tab) => { const active = Number(tab.dataset.step) === currentStep; tab.classList.toggle("active", active); tab.setAttribute("aria-selected", String(active)); });
    previous.disabled = currentStep === 1; next.hidden = currentStep === 3; save.hidden = currentStep !== 3;
    persistDraft();
  };
  const validateCurrentStep = () => {
    const active = steps.find((step) => Number(step.dataset.step) === currentStep);
    const invalidField = active.querySelector(":invalid");
    if (!invalidField) return true;
    invalidField.setAttribute("aria-invalid", "true");
    setStatus(status, `Заповніть коректно обов’язкові поля кроку ${currentStep}.`, true);
    invalidField.reportValidity();
    return false;
  };
  tabs.forEach((tab) => tab.addEventListener("click", () => {
    const targetStep = Number(tab.dataset.step);
    if (targetStep > currentStep && !validateCurrentStep()) return;
    currentStep = targetStep;
    updateStep();
  }));
  next.addEventListener("click", () => {
    if (currentStep >= 3) return;
    if (validateCurrentStep()) { currentStep += 1; updateStep(); }
  });
  previous.addEventListener("click", () => { currentStep -= 1; updateStep(); });
  form.addEventListener("invalid", (event) => {
    event.target.setAttribute("aria-invalid", "true");
  }, true);
  form.addEventListener("input", (event) => {
    if (event.target.validity?.valid) {
      event.target.removeAttribute("aria-invalid");
      if (status.classList.contains("is-error")) setStatus(status, "");
    }
    persistDraft();
  });
  form.addEventListener("change", persistDraft);
  form.addEventListener("keydown", (event) => {
    const target = event.target;
    if (
      event.key === "Enter"
      && !event.isComposing
      && target instanceof HTMLInputElement
      && implicitSubmitInputTypes.has(target.type)
    ) event.preventDefault();
  });

  let currentUserId;
  try {
    const [references, mappings, nextId, currentUser] = await Promise.all([getReferenceValues(token), getGradeMappings(), getNextReportId(token), getCurrentUser(token)]);
    document.getElementById("report-id-preview").value = nextId.report_id;
    document.querySelectorAll("[data-reference-category]").forEach((select) => {
      const entries = references.filter((entry) => entry.category === select.dataset.referenceCategory);
      setOptions(select, entries, "code", "label", ["girdle_thickness", "culet_size"].includes(select.dataset.referenceCategory));
    });
    document.querySelectorAll("[data-grade-category]").forEach((select) => {
      const entries = mappings.filter((entry) => entry.category === select.dataset.gradeCategory);
      setOptions(select, entries, "grade_value", "grade_label");
    });
    mappings.forEach((entry) => gradeLabels.set(`${entry.category}:${entry.grade_value}`, entry.grade_label));
    renderInitialFinish();
    currentUserId = currentUser.expert_id;
    draftStorage = createWizardDraftStorage({ userId: currentUserId });
  } catch (error) { setStatus(status, `Не вдалося завантажити довідники: ${error.message}`, true); return; }

  workSessionTracker = createWizardWorkSessionTracker({ form, token, userId: currentUserId });

  [["plotting-image", "plotting-preview"], ["real-image", "stone-preview"]].forEach(([inputId, previewId]) => {
    const input = document.getElementById(inputId);
    input.addEventListener("change", () => {
      const file = input.files[0];
      document.querySelector(`[data-file-name-for="${inputId}"]`).textContent = file ? file.name : "Файл не вибрано";
      if (file) document.getElementById(previewId).src = URL.createObjectURL(file);
    });
  });

  let previewTimer;
  schedulePreview = () => {
    clearTimeout(previewTimer);
    const data = new FormData(form);
    if (requiredPreviewNames.every((name) => data.get(name) !== "")) previewTimer = setTimeout(async () => {
      try {
        const preview = await previewReportCalculation(calculationInput(data), token);
        document.getElementById("res-prop").textContent = gradeLabels.get(`proportions:${preview.system_proportions_grade}`) || preview.system_proportions_grade;
        document.getElementById("res-pol").textContent = gradeLabels.get(`polish:${data.get("polish_grade")}`) || data.get("polish_grade");
        document.getElementById("res-sym").textContent = gradeLabels.get(`symmetry:${data.get("symmetry_grade")}`) || data.get("symmetry_grade");
        document.getElementById("res-final").textContent = gradeLabels.get(`cut:${preview.system_cut_grade}`) || preview.system_cut_grade;
        const price = document.getElementById("res-price");
        const priceMarker = document.getElementById("price-provider-marker");
        const priceSource = document.getElementById("market-reference-preview-source");
        const providerNames = { openfacet: "OpenFacet" };
        const providerMarkers = { openfacet: "of" };
        price.textContent = preview.system_market_reference_usd === null
          ? "--"
          : `USD ${new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(preview.system_market_reference_usd)}`;
        priceMarker.hidden = preview.system_market_reference_usd === null;
        priceMarker.textContent = providerMarkers[preview.market_reference_provider_code] || preview.market_reference_provider_code || "";
        priceSource.textContent = preview.system_market_reference_usd === null
          ? "Немає доступного системного орієнтиру для введених характеристик."
          : `${providerNames[preview.market_reference_provider_code] || preview.market_reference_provider_code} · знімок #${preview.market_reference_snapshot_id}. Значення буде зафіксовано під час збереження чернетки.`;
      } catch { /* invalid values are handled by native fields */ }
    }, 300);
  };
  form.addEventListener("input", schedulePreview);
  form.addEventListener("change", schedulePreview);

  const resetFileInputs = () => {
    [["plotting-image", "plotting-preview", "/img/plotting-placeholder.svg"], ["real-image", "stone-preview", "/img/stone-placeholder.svg"]].forEach(([inputId, previewId, placeholder]) => {
      const input = document.getElementById(inputId);
      input.value = "";
      document.querySelector(`[data-file-name-for="${inputId}"]`).textContent = "Файл не вибрано";
      document.getElementById(previewId).src = placeholder;
    });
  };
  const resetForm = () => {
    suppressDraftPersistence = true;
    for (const field of form.elements) {
      if (!field.name || field.disabled) continue;
      if (field.type === "file") { field.value = ""; continue; }
      if (field.type === "checkbox" || field.type === "radio") field.checked = false;
      else if (field.tagName === "SELECT") field.selectedIndex = -1;
      else field.value = "";
    }
    document.getElementById("examination-date").valueAsDate = new Date();
    resetFileInputs();
    currentStep = 1;
    renderInitialFinish();
    updateStep();
    schedulePreview();
    suppressDraftPersistence = false;
  };
  const startNew = () => {
    draftStorage.clear();
    workSessionTracker.clear();
    hasUnsavedDraft = false;
    resetForm();
    updateClearDraftButton();
    setStatus(status, "Почато нове незбережене введення.");
  };
  const restoreDraft = (draft) => {
    suppressDraftPersistence = true;
    draftStorage.restore(form, draft);
    currentStep = draft.current_step;
    hasUnsavedDraft = true;
    renderInitialFinish();
    updateStep();
    suppressDraftPersistence = false;
    updateClearDraftButton();
    schedulePreview();
    setStatus(status, "Незбережене введення відновлено. Вкладення додайте повторно.");
  };
  const storedDraft = draftStorage.read();
  if (storedDraft) {
    restoreDialog.addEventListener("cancel", (event) => event.preventDefault());
    document.getElementById("wizard-restore").addEventListener("click", () => { restoreDialog.close(); restoreDraft(storedDraft); });
    document.getElementById("wizard-start-new").addEventListener("click", () => { restoreDialog.close(); startNew(); });
    restoreDialog.showModal();
  } else {
    resetForm();
  }
  clearDraftButton.addEventListener("click", () => clearDialog.showModal());
  document.getElementById("wizard-clear-dialog-close").addEventListener("click", () => clearDialog.close());
  document.getElementById("wizard-clear-cancel").addEventListener("click", () => clearDialog.close());
  document.getElementById("wizard-clear-confirm").addEventListener("click", () => { clearDialog.close(); startNew(); });
  window.addEventListener("beforeunload", (event) => {
    if (!hasUnsavedDraft) return;
    event.preventDefault();
    event.returnValue = "";
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateCurrentStep() || !form.reportValidity()) return;
    save.disabled = true; setStatus(status, "Збереження чернетки…");
    try {
      const data = new FormData(form);
      const wizardSessionId = await workSessionTracker.getOrStart();
      const created = await createDomainReport({
        examination_date: data.get("examination_date"), stone: stoneFromForm(data),
        expert_comment: data.get("expert_comment") || null, wizard_session_id: wizardSessionId,
      }, token);
      draftStorage.clear();
      hasUnsavedDraft = false;
      updateClearDraftButton();
      workSessionTracker.clear();
      for (const [id, type] of [["plotting-image", "plotting_diagram"], ["real-image", "stone_photo"]]) { const file = document.getElementById(id).files[0]; if (file) await uploadReportMedia(created.report_id, type, file, token); }
      window.location.assign(`/dashboard.html?created=${encodeURIComponent(created.report_id)}`);
    } catch (error) { setStatus(status, `Не вдалося зберегти чернетку: ${error.message}`, true); save.disabled = false; }
  });
  updateStep();
}
