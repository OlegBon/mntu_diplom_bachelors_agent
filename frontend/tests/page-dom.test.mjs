import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { JSDOM } from "jsdom";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const loginPath = path.resolve(testDir, "../dist/login.html");
const createReportPath = path.resolve(testDir, "../dist/create-report.html");
const dashboardPath = path.resolve(testDir, "../dist/dashboard.html");

test("built login page exposes accessible authentication fields", async () => {
  const html = await readFile(loginPath, "utf8");
  const document = new JSDOM(html).window.document;

  assert.equal(document.querySelector("#login-form")?.tagName, "FORM");
  assert.equal(document.querySelector("#username")?.getAttribute("autocomplete"), "username");
  assert.equal(document.querySelector("#password")?.getAttribute("autocomplete"), "current-password");
});

test("built report wizard provides private media inputs and explicit fallbacks", async () => {
  const html = await readFile(createReportPath, "utf8");
  const document = new JSDOM(html).window.document;

  for (const inputId of ["plotting-image", "real-image"]) {
    const input = document.querySelector(`#${inputId}`);
    assert.equal(input?.getAttribute("type"), "file");
    assert.equal(input?.getAttribute("accept"), "image/jpeg,image/png,image/webp");
  }
  assert.equal(document.querySelector("#plotting-preview")?.getAttribute("src"), "/img/plotting-placeholder.svg");
  assert.equal(document.querySelector("#stone-preview")?.getAttribute("src"), "/img/stone-placeholder.svg");
});

test("built dashboard uses text-only primary controls and pagination", async () => {
  const html = await readFile(dashboardPath, "utf8");
  const document = new JSDOM(html).window.document;

  assert.equal(document.querySelector("#create-report-action")?.textContent.trim(), "Новий звіт");
  assert.equal(document.querySelector("#toggle-filters")?.textContent.trim(), "Фільтри");
  assert.equal(document.querySelector(".pagination .page-btn")?.textContent.trim(), "Попередня");
  assert.equal(document.querySelector(".actions .table-action")?.textContent.trim(), "Редагувати");
});
