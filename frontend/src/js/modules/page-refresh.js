const REFRESH_INTERVAL_MS = 30_000;

export function registerVisibleDataRefresh(refresh, { canRefresh = () => true, intervalMs = REFRESH_INTERVAL_MS } = {}) {
  let inFlight = false;
  const run = async () => {
    if (document.visibilityState === "hidden" || inFlight || !canRefresh()) return;
    inFlight = true;
    try { await refresh(); } catch { /* The page keeps its last verified rendering until the next refresh. */ } finally { inFlight = false; }
  };
  const onVisibility = () => { if (document.visibilityState === "visible") void run(); };
  const onFocus = () => { void run(); };
  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("focus", onFocus);
  const intervalId = window.setInterval(() => { void run(); }, intervalMs);
  return () => {
    document.removeEventListener("visibilitychange", onVisibility);
    window.removeEventListener("focus", onFocus);
    window.clearInterval(intervalId);
  };
}
