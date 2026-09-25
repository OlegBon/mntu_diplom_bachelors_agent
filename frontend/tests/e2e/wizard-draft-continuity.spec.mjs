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

async function mockWizardDependencies(page) {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 2, username: "expert_1", role: "gemologist" } }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: references }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: mappings }));
  await page.route("**/reports/next-id", (route) => route.fulfill({ json: { report_id: "DR-01010" } }));
  await page.route("**/report-wizard-sessions", (route) => route.fulfill({ json: { wizard_session_id: "11111111-1111-1111-1111-111111111111" } }));
}

test("wizard restores an unsaved tab draft only after the expert confirms it", async ({ page }) => {
  await mockWizardDependencies(page);
  await page.goto("/create-report.html");

  await page.locator("#shape").selectOption("Round");
  await page.locator("#origin").selectOption("natural");
  await page.locator("#carat-weight").fill("1.25");
  await page.locator("#color-grade").selectOption("0");
  await page.locator("#clarity-grade").selectOption("0");
  await page.locator("#next-btn").click();
  await expect(page.locator(".step-content[data-step='2']")).toBeVisible();

  await page.reload();
  await expect(page.locator("#wizard-restore-dialog")).toBeVisible();
  await expect(page.locator("#wizard-restore-dialog")).toContainText("Вкладення не відновлюються");
  await expect(page.locator(".step-content[data-step='1']")).toBeVisible();

  await page.locator("#wizard-restore").click();
  await expect(page.locator(".step-content[data-step='2']")).toBeVisible();
  await expect(page.locator("#shape")).toHaveValue("Round");
  await expect(page.locator("#carat-weight")).toHaveValue("1.25");
  await expect(page.locator("#clear-wizard-draft")).toBeVisible();

  await page.locator("#clear-wizard-draft").click();
  await expect(page.locator("#wizard-clear-dialog")).toBeVisible();
  await page.locator("#wizard-clear-confirm").click();

  await expect(page.locator("#shape")).toHaveValue("Round");
  await expect(page.locator("#carat-weight")).toHaveValue("");
  await expect(page.locator("#clear-wizard-draft")).toBeHidden();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("diamant-id:wizard-draft:v1:user:2"))).toBeNull();
});

test("wizard uses a project dialog before an in-app navigation", async ({ page }) => {
  await mockWizardDependencies(page);
  await page.goto("/create-report.html");
  await page.locator("#carat-weight").fill("1.25");

  await page.locator(".logo").click();
  await expect(page.locator("#wizard-leave-dialog")).toBeVisible();
  await page.locator("#wizard-leave-cancel").click();
  await expect(page).toHaveURL(/create-report\.html/);

  await page.locator(".logo").click();
  await page.locator("#wizard-leave-confirm").click();
  await expect(page).toHaveURL(/\/$/);
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("diamant-id:wizard-draft:v1:user:2"))).not.toBeNull();
});

test("wizard removes its local draft only after the report is created", async ({ page }) => {
  await mockWizardDependencies(page);
  await page.route("**/reports", (route) => route.fulfill({ json: { report_id: "DR-01010" } }));
  await page.goto("/create-report.html");

  await page.locator("#shape").selectOption("Round");
  await page.locator("#origin").selectOption("natural");
  await page.locator("#carat-weight").fill("1.25");
  await page.locator("#color-grade").selectOption("0");
  await page.locator("#clarity-grade").selectOption("0");
  await page.locator("#next-btn").click();
  await page.locator("#measurements-length").fill("6");
  await page.locator("#measurements-width").fill("6");
  await page.locator("#measurements-depth").fill("3.8");
  await page.locator("#table-percent").fill("58");
  await page.locator("#depth-percent").fill("61");
  await page.locator("#crown-angle").fill("34.5");
  await page.locator("#pavilion-angle").fill("40.8");
  await page.locator("#next-btn").click();
  await page.locator("#polish-grade").selectOption("0");
  await page.locator("#symmetry-grade").selectOption("0");
  await page.locator("#fluorescence-grade").selectOption("0");
  await page.locator("#treatment-status").selectOption("not_assessed");
  await page.locator("#identification-status").selectOption("preliminary");

  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("diamant-id:wizard-draft:v1:user:2"))).not.toBeNull();
  await page.locator("#save-btn").click();
  await expect(page).toHaveURL(/dashboard\.html\?created=DR-01010/);
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("diamant-id:wizard-draft:v1:user:2"))).toBeNull();
});
