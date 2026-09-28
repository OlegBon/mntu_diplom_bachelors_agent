import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { JSDOM } from "jsdom";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const demoReportsPath = path.resolve(testDir, "../dist/demo-reports.html");

test("built demo page exposes an enabled provider analytics tab and read-only panel", async () => {
  const html = await readFile(demoReportsPath, "utf8");
  const document = new JSDOM(html).window.document;

  const tab = document.querySelector("#demo-tab-providers");
  assert.equal(tab?.getAttribute("data-demo-tab"), "providers");
  assert.equal(tab?.hasAttribute("disabled"), false);
  assert.equal(tab?.getAttribute("aria-controls"), "demo-providers-panel");
  assert.equal(document.querySelector("#demo-providers-panel")?.getAttribute("role"), "tabpanel");
  assert.equal(document.querySelector("#demo-providers-status")?.getAttribute("role"), "status");
  assert.equal(document.querySelector("#demo-providers-results")?.getAttribute("aria-live"), "polite");
  assert.equal(document.querySelector("#demo-provider-dialog")?.tagName, "DIALOG");
  assert.equal(document.querySelector("#demo-provider-dialog-content")?.id, "demo-provider-dialog-content");
});

test("built demo page exposes synthetic operational quality with the shared period controls", async () => {
  const html = await readFile(demoReportsPath, "utf8");
  const document = new JSDOM(html).window.document;

  assert.equal(document.querySelector("#demo-tab-quality")?.getAttribute("data-demo-tab"), "quality");
  assert.equal(document.querySelector("#demo-tab-quality")?.getAttribute("aria-controls"), "demo-quality-panel");
  assert.equal(document.querySelector("#demo-quality-panel")?.getAttribute("role"), "tabpanel");
  assert.equal(document.querySelector("#demo-quality-status")?.getAttribute("role"), "status");
  assert.equal(document.querySelector("#demo-quality-results")?.getAttribute("aria-live"), "polite");
});
