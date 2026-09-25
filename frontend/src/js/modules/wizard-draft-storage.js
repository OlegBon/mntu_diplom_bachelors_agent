const STORAGE_PREFIX = "diamant-id:wizard-draft";
const SCHEMA_VERSION = 1;

function storageKey(userId) {
  return `${STORAGE_PREFIX}:v${SCHEMA_VERSION}:user:${userId}`;
}

function canUse(storage, method) {
  try {
    return typeof storage?.[method] === "function";
  } catch {
    return false;
  }
}

function serializableFields(form) {
  const values = {};
  for (const field of form.elements) {
    if (!field.name || field.disabled || field.type === "file") continue;
    if (field.type === "radio" && !field.checked) continue;
    values[field.name] = field.type === "checkbox" ? Boolean(field.checked) : field.value;
  }
  return values;
}

function hasMeaningfulValue(values) {
  return Object.values(values).some((value) => value === true || (typeof value === "string" && value.trim() !== ""));
}

export function createWizardDraftStorage({ userId, storage = globalThis.sessionStorage }) {
  const normalizedUserId = String(userId);
  const key = storageKey(normalizedUserId);

  function clear() {
    if (!canUse(storage, "removeItem")) return;
    try { storage.removeItem(key); } catch { /* Storage can be unavailable in private contexts. */ }
  }

  function read() {
    if (!canUse(storage, "getItem")) return null;
    try {
      const raw = storage.getItem(key);
      if (!raw) return null;
      const draft = JSON.parse(raw);
      if (
        draft?.schema_version !== SCHEMA_VERSION
        || String(draft.user_id) !== normalizedUserId
        || !Number.isInteger(draft.current_step)
        || draft.current_step < 1
        || draft.current_step > 3
        || !draft.values
        || typeof draft.values !== "object"
        || !hasMeaningfulValue(draft.values)
      ) {
        clear();
        return null;
      }
      return draft;
    } catch {
      clear();
      return null;
    }
  }

  function save(form, currentStep) {
    const values = serializableFields(form);
    if (!hasMeaningfulValue(values)) {
      clear();
      return false;
    }
    if (!canUse(storage, "setItem")) return false;
    const payload = {
      schema_version: SCHEMA_VERSION,
      user_id: normalizedUserId,
      current_step: currentStep,
      values,
      saved_at: new Date().toISOString(),
    };
    try {
      storage.setItem(key, JSON.stringify(payload));
      return true;
    } catch {
      return false;
    }
  }

  function restore(form, draft) {
    for (const [name, value] of Object.entries(draft.values)) {
      const field = form.elements.namedItem(name);
      if (!field || field.type === "file") continue;
      if (field.type === "checkbox") field.checked = Boolean(value);
      else field.value = String(value);
    }
  }

  return { clear, read, restore, save };
}
