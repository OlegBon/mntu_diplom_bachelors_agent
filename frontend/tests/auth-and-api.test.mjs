import assert from "node:assert/strict";
import test from "node:test";

import { getNextReportId, getReportDashboard, getReferenceValues, loginUser } from "../src/js/modules/api.js";
import { checkAuth, logout } from "../src/js/modules/auth.js";

function installBrowserStubs() {
  const storage = new Map();
  globalThis.localStorage = {
    clear: () => storage.clear(),
    getItem: (key) => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
  };
  globalThis.window = { location: { href: "" } };
  return storage;
}

test("checkAuth follows presence of a token", () => {
  const storage = installBrowserStubs();

  assert.equal(checkAuth(), false);
  storage.set("token", "test-token");
  assert.equal(checkAuth(), true);
});

test("logout clears local session and returns to landing page", () => {
  const storage = installBrowserStubs();
  storage.set("token", "test-token");

  logout();

  assert.equal(storage.size, 0);
  assert.equal(window.location.href, "/");
});

test("loginUser returns the API access token", async () => {
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({ access_token: "test-token" }),
  });

  assert.equal(await loginUser("test-user", "test-password"), "test-token");
});

test("loginUser rejects an unsuccessful response", async () => {
  globalThis.fetch = async () => ({ ok: false });
  const originalConsoleError = console.error;
  console.error = () => {};

  try {
    await assert.rejects(() => loginUser("test-user", "wrong-password"));
  } finally {
    console.error = originalConsoleError;
  }
});

test("getReportDashboard omits empty filters and forwards the bearer token", async () => {
  let requestedUrl = "";
  let requestedHeaders;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedHeaders = options.headers;
    return { ok: true, json: async () => ({ items: [], total: 0, page: 1, page_size: 25, total_pages: 0 }) };
  };

  await getReportDashboard(
    { page: 1, page_size: 25, search: "", report_status: "", sort: "report_date_desc" },
    "test-token",
  );

  assert.match(requestedUrl, /page=1/);
  assert.doesNotMatch(requestedUrl, /search=|report_status=/);
  assert.equal(requestedHeaders.Authorization, "Bearer test-token");
});

test("wizard API reads protected references and the non-reserving next report ID", async () => {
  const paths = [];
  globalThis.fetch = async (url, options) => {
    paths.push([url, options.headers.Authorization]);
    return { ok: true, json: async () => ({ report_id: "DR-01001" }) };
  };

  await getReferenceValues("test-token");
  assert.equal((await getNextReportId("test-token")).report_id, "DR-01001");
  assert.deepEqual(paths, [
    ["http://127.0.0.1:8000/reference-values", "Bearer test-token"],
    ["http://127.0.0.1:8000/reports/next-id", "Bearer test-token"],
  ]);
});
