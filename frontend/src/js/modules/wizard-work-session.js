import { startWizardWorkSession } from "./api.js";

const TAB_STORAGE_KEY = "diamond-id:wizard-tab-id";
const SESSION_STORAGE_KEY = "diamond-id:wizard-work-session-id";

function makeId() {
  return crypto.randomUUID();
}

function tabId() {
  let value = sessionStorage.getItem(TAB_STORAGE_KEY);
  if (!value) {
    value = makeId();
    sessionStorage.setItem(TAB_STORAGE_KEY, value);
  }
  return value;
}

export function createWizardWorkSessionTracker({ form, token }) {
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
  let pendingStart = null;

  async function start() {
    if (sessionId || document.visibilityState !== "visible") return sessionId;
    if (pendingStart) return pendingStart;
    pendingStart = startWizardWorkSession({ tab_id: tabId() }, token)
      .then((state) => {
        sessionId = state.wizard_session_id;
        sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
        return sessionId;
      })
      .catch(() => null)
      .finally(() => { pendingStart = null; });
    return pendingStart;
  }

  function handleInteraction() {
    void start();
  }

  form.addEventListener("pointerdown", handleInteraction);
  form.addEventListener("focusin", handleInteraction);
  form.addEventListener("input", handleInteraction);
  form.addEventListener("change", handleInteraction);

  return {
    getOrStart: start,
    clear() {
      sessionId = null;
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    },
  };
}
