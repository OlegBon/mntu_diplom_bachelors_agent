import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { JSDOM } from "jsdom";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const page = (name) => path.resolve(testDir, `../dist/${name}.html`);

test("built profile keeps username and role read-only while exposing password confirmation", async () => {
  const document = new JSDOM(await readFile(page("profile"), "utf8")).window.document;
  assert.equal(document.querySelector("[data-profile-page]")?.hasAttribute("data-protected-page"), true);
  assert.equal(document.querySelector("#profile-username")?.disabled, true);
  assert.equal(document.querySelector("#profile-role")?.disabled, true);
  assert.equal(document.querySelector("#password-form [name=confirm_password]")?.getAttribute("type"), "password");
});

test("built admin pages have real account and read-only reference controls", async () => {
  const experts = new JSDOM(await readFile(page("experts"), "utf8")).window.document;
  const references = new JSDOM(await readFile(page("references"), "utf8")).window.document;
  assert.equal(experts.querySelector("[data-admin-users-page]")?.hasAttribute("data-protected-page"), true);
  assert.equal(experts.querySelector("#admin-user-create-form")?.tagName, "FORM");
  assert.equal(experts.querySelector("#admin-users-body")?.tagName, "TBODY");
  assert.equal(references.querySelector("[data-reference-catalog-page]")?.hasAttribute("data-protected-page"), true);
  assert.equal(references.querySelector("#reference-catalog")?.tagName, "DIV");
  assert.equal(references.querySelector("form"), null);
});
