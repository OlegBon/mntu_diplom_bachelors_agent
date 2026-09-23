import { ApiRequestError, signalReportWorkSession } from "./api.js";

const SIGNAL_INTERVAL_MS = 30_000;

function tabIdForReport(reportId) {
  const key = `diamant-id:work-session-tab:${reportId}`;
  try {
    let value = sessionStorage.getItem(key);
    if (!value) {
      value = crypto.randomUUID();
      sessionStorage.setItem(key, value);
    }
    return value;
  } catch {
    return crypto.randomUUID();
  }
}

/** Track only user-initiated activity in one editable, saved draft tab. */
export function createDraftWorkSessionTracker({ reportId, token, form }) {
  const tabId = tabIdForReport(reportId);
  let enabled = false;
  let active = false;
  let pendingSignal = null;
  let lastSignalAt = 0;

  async function signal(action, { quiet = true } = {}) {
    if (!enabled) return null;
    if (pendingSignal) await pendingSignal;
    const request = (async () => {
    try {
      const result = await signalReportWorkSession(reportId, { action, tab_id: tabId }, token);
      active = result.is_active;
      lastSignalAt = Date.now();
      return result;
    } catch (error) {
      active = false;
      if (!quiet) throw error;
      return null;
    } finally {
      if (pendingSignal === request) pendingSignal = null;
    }
    })();
    pendingSignal = request;
    return request;
  }

  async function recordActivity() {
    if (!enabled || document.visibilityState !== "visible") return;
    if (!active) {
      await signal("start");
      return;
    }
    if (Date.now() - lastSignalAt >= SIGNAL_INTERVAL_MS) await signal("heartbeat");
  }

  function pause() {
    if (active) signal("pause");
  }

  function setEnabled(value, { pauseOnDisable = true } = {}) {
    if (!value && enabled && pauseOnDisable) pause();
    enabled = value;
  }

  async function checkpointSave() {
    if (active) await signal("save");
  }

  form.addEventListener("input", recordActivity);
  form.addEventListener("change", recordActivity);
  form.addEventListener("focusin", recordActivity);
  form.addEventListener("pointerdown", recordActivity);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") pause();
  });
  window.addEventListener("pagehide", pause);

  return { checkpointSave, recordActivity, setEnabled };
}
