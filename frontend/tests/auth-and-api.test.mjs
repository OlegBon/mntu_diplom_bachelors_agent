import assert from "node:assert/strict";
import test from "node:test";

import { loginUser } from "../src/js/modules/api.js";
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
