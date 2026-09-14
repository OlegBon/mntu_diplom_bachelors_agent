import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { JSDOM } from "jsdom";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const loginPath = path.resolve(testDir, "../dist/login.html");

test("built login page exposes accessible authentication fields", async () => {
  const html = await readFile(loginPath, "utf8");
  const document = new JSDOM(html).window.document;

  assert.equal(document.querySelector("#login-form")?.tagName, "FORM");
  assert.equal(document.querySelector("#username")?.getAttribute("autocomplete"), "username");
  assert.equal(document.querySelector("#password")?.getAttribute("autocomplete"), "current-password");
});
