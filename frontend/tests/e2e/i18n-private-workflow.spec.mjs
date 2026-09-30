import { expect, test } from "@playwright/test";

const mappings = [
  { category: "color", grade_value: 0, grade_label: "D" },
  { category: "clarity", grade_value: 0, grade_label: "FL" },
  { category: "polish", grade_value: 0, grade_label: "Excellent" },
  { category: "symmetry", grade_value: 0, grade_label: "Excellent" },
  { category: "fluorescence", grade_value: 0, grade_label: "None" },
  { category: "proportions", grade_value: 0, grade_label: "Excellent" },
  { category: "cut", grade_value: 0, grade_label: "Excellent" },
];

test("locale switch preserves an in-progress private report wizard", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 2, username: "expert_1", role: "gemologist" } }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: mappings }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: [
    { category: "shape", code: "Round", label: "Round" },
    { category: "origin", code: "natural", label: "Natural" },
    { category: "girdle_thickness", code: "medium", label: "Medium" },
    { category: "culet_size", code: "none", label: "None" },
  ] }));
  await page.route("**/reports/next-id", (route) => route.fulfill({ json: { report_id: "DR-2026-NEW" } }));

  await page.goto("/create-report.html?source=locale-check#step-1");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.locator("#shape").selectOption("Round");
  await page.locator("#origin").selectOption("natural");
  await page.locator("#carat-weight").fill("1.25");
  await page.locator("#color-grade").selectOption("0");
  await page.locator("#clarity-grade").selectOption("0");
  await page.locator("#next-btn").click();
  await expect(page.locator(".step-content[data-step='2']")).toBeVisible();

  await page.getByRole("button", { name: "Ukrainian" }).click();

  await expect(page.locator("html")).toHaveAttribute("lang", "uk");
  await expect(page.locator(".step-content[data-step='2']")).toBeVisible();
  await expect(page.locator("#carat-weight")).toHaveValue("1.25");
  await expect(page.locator("#shape")).toHaveValue("Round");
  await expect(page).toHaveURL(/source=locale-check/);
  await expect(page).toHaveURL(/lang=uk/);
  await expect(page).toHaveURL(/#step-1$/);
});
