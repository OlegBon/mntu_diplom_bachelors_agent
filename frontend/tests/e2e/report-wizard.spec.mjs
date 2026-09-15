import { expect, test } from "@playwright/test";

const references = [
  ["shape", "Round", "Round"],
  ["origin", "natural", "Natural"],
  ["girdle_thickness", "medium", "Medium"],
  ["culet_size", "none", "None"],
  ["treatment_status", "not_assessed", "Not assessed"],
  ["identification_status", "preliminary", "Preliminary"],
].map(([category, code, label]) => ({ category, code, label }));

const mappings = ["color", "clarity", "cut", "polish", "symmetry", "fluorescence"]
  .map((category) => ({ category, grade_value: 0, grade_label: "Excellent" }));

test("gemologist creates a draft through the three-step wizard", async ({ page }) => {
  let createdPayload;
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 2, username: "expert_1", role: "gemologist" } }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: references }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: mappings }));
  await page.route("**/reports/next-id", (route) => route.fulfill({ json: { report_id: "DR-01001" } }));
  await page.route("**/reports/preview", (route) => route.fulfill({ json: {
    system_proportions_grade: 0, system_cut_grade: 0, calculation_rule_version: "idc-demo-v1", demo_price_usd: "5400.00",
  } }));
  await page.route("**/reports", async (route) => {
    createdPayload = route.request().postDataJSON();
    await route.fulfill({ json: { report_id: "DR-01001" } });
  });

  await page.goto("/create-report.html");
  await expect(page.locator("#report-id-preview")).toHaveValue("DR-01001");

  await page.locator("#shape").selectOption("Round");
  await page.locator("#origin").selectOption("natural");
  await page.locator("#carat-weight").fill("1.25");
  await page.locator("#color-grade").selectOption("0");
  await page.locator("#clarity-grade").selectOption("0");
  await page.locator("#next-btn").click();

  await page.locator("#measurements-length").fill("6.0");
  await page.locator("#measurements-width").fill("6.0");
  await page.locator("#measurements-depth").fill("3.8");
  await page.locator("#table-percent").fill("58");
  await page.locator("#depth-percent").fill("61");
  await page.locator("#crown-angle").fill("34.5");
  await page.locator("#pavilion-angle").fill("40.8");
  await page.locator("#girdle-thickness").selectOption("medium");
  await page.locator("#culet-size").selectOption("none");
  await expect(page.locator("#res-price")).toContainText("USD 5,400.00");
  await page.locator("#next-btn").click();

  await page.locator("#polish-grade").selectOption("0");
  await page.locator("#symmetry-grade").selectOption("0");
  await page.locator("#fluorescence-grade").selectOption("0");
  await page.locator("#treatment-status").selectOption("not_assessed");
  await page.locator("#identification-status").selectOption("preliminary");
  await page.locator("#save-btn").click();

  await expect(page).toHaveURL(/dashboard\.html\?created=DR-01001/);
  expect(createdPayload.examination_date).toBeTruthy();
  expect(createdPayload.stone.market_status).toBe("not_for_sale");
  expect(createdPayload.stone.carat_weight).toBe(1.25);
});
