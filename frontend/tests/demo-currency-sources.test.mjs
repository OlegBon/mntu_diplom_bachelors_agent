import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { JSDOM } from "jsdom";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const demoReportsPath = path.resolve(testDir, "../dist/demo-reports.html");

test("built demo page separates unsliced currency sources from date-sliced analytics", async () => {
  const html = await readFile(demoReportsPath, "utf8");
  const document = new JSDOM(html).window.document;

  assert.deepEqual(
    [...document.querySelectorAll("[data-demo-tab]")].map((tab) => tab.dataset.demoTab),
    ["reports", "stones", "experts", "narratives", "administrators", "providers", "currency"],
  );
  assert.equal(document.querySelector("#demo-tab-narratives")?.getAttribute("aria-controls"), "demo-narratives-panel");
  assert.equal(document.querySelector("#demo-narratives-results")?.getAttribute("aria-live"), "polite");
  assert.equal(document.querySelector("#demo-tab-currency")?.getAttribute("aria-controls"), "demo-currency-panel");
  assert.equal(document.querySelector("#demo-currency-panel")?.getAttribute("role"), "tabpanel");
  assert.equal(document.querySelector("#demo-currency-status")?.getAttribute("role"), "status");
  assert.equal(document.querySelector("#demo-workflow-controls")?.classList.contains("demo-time-slice"), true);
});
