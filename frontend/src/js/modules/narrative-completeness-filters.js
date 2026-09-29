const FILTER_NAME = "empty_narrative";
const PRESENCE_NAME = "narrative_presence";
const ALLOWED_FILTERS = new Set([
  "identification_method", "identification_conclusion", "expert_comment", "status_transition_reason",
]);

export function narrativeCompletenessFromUrl(params) {
  return params.getAll(FILTER_NAME)
    .flatMap((value) => value.split(","))
    .filter((value) => ALLOWED_FILTERS.has(value));
}

export function narrativePresenceFromUrl(params) {
  return params.get(PRESENCE_NAME) === "filled" ? "filled" : "empty";
}

export function applyNarrativeCompleteness(form, selected, presence = "empty") {
  const values = new Set(selected);
  form.querySelectorAll(`[name="${FILTER_NAME}"]`).forEach((control) => {
    control.checked = values.has(control.value);
  });
  form.querySelectorAll(`[name="${PRESENCE_NAME}"]`).forEach((control) => {
    control.checked = control.value === presence;
  });
}

export function readNarrativeCompleteness(form) {
  return [...form.querySelectorAll(`[name="${FILTER_NAME}"]:checked`)].map((control) => control.value);
}

export function readNarrativePresence(form) {
  return form.querySelector(`[name="${PRESENCE_NAME}"]:checked`)?.value === "filled" ? "filled" : "empty";
}
