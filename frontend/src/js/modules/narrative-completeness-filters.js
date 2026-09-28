const FILTER_NAME = "empty_narrative";
const ALLOWED_FILTERS = new Set([
  "identification_method", "identification_conclusion", "expert_comment", "status_transition_reason",
]);

export function narrativeCompletenessFromUrl(params) {
  return (params.get(FILTER_NAME) || "").split(",").filter((value) => ALLOWED_FILTERS.has(value));
}

export function applyNarrativeCompleteness(form, selected) {
  const values = new Set(selected);
  form.querySelectorAll(`[name="${FILTER_NAME}"]`).forEach((control) => {
    control.checked = values.has(control.value);
  });
}

export function readNarrativeCompleteness(form) {
  return [...form.querySelectorAll(`[name="${FILTER_NAME}"]:checked`)].map((control) => control.value);
}
