import assert from "node:assert/strict";
import test from "node:test";

import { ApiRequestError } from "../src/js/modules/api.js";
import { clearSession, isConfirmedUnauthorized } from "../src/js/modules/auth.js";

function installStorage() {
  const storage = new Map();
  globalThis.localStorage = {
    getItem: (key) => storage.get(key) ?? null,
    removeItem: (key) => storage.delete(key),
    setItem: (key, value) => storage.set(key, value),
  };
  return storage;
}

test("only a confirmed 401 is treated as an invalid session", () => {
  assert.equal(isConfirmedUnauthorized(new ApiRequestError("Unauthorized", 401)), true);
  assert.equal(isConfirmedUnauthorized(new ApiRequestError("Server error", 500)), false);
  assert.equal(isConfirmedUnauthorized(new TypeError("Network request failed")), false);
});

test("clearing an invalid session preserves unrelated local state", () => {
  const storage = installStorage();
  storage.set("token", "test-token");
  storage.set("username", "test-user");
  storage.set("role", "admin");
  storage.set("demo_access_enabled", "true");
  storage.set("unrelated-local-preference", "keep");

  clearSession();

  assert.equal(storage.get("token"), undefined);
  assert.equal(storage.get("username"), undefined);
  assert.equal(storage.get("role"), undefined);
  assert.equal(storage.get("demo_access_enabled"), undefined);
  assert.equal(storage.get("unrelated-local-preference"), "keep");
});
