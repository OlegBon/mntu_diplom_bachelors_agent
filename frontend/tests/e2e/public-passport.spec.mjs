import { expect, test } from "@playwright/test";

test("guest reads only the safe public passport projection", async ({ page }) => {
  await page.route("**/public/passports/public-id", (route) => route.fulfill({ json: {
    public_id: "public-id",
    report_id: "DR-01001",
    issued_at: "2026-09-16T09:00:00Z",
    examination_date: "2026-09-15",
    shape: "Round",
    carat_weight: "1.00",
    color_grade: 0,
    clarity_grade: 0,
    measurements_length: "6.00",
    measurements_width: "6.00",
    measurements_depth: "3.80",
    system_proportions_grade: 0,
    system_cut_grade: 0,
    expert_proportions_grade: 0,
    expert_cut_grade: 0,
    origin: "natural",
    treatment_status: "none_detected",
    identification_status: "confirmed",
  } }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: [
    { category: "color", grade_value: 0, grade_label: "D" },
    { category: "clarity", grade_value: 0, grade_label: "FL" },
    { category: "proportions", grade_value: 0, grade_label: "Excellent" },
    { category: "cut", grade_value: 0, grade_label: "Excellent" },
  ] }));

  await page.goto("/passport.html?id=public-id");

  await expect(page.locator("#public-passport-title")).toHaveText("Паспорт DR-01001");
  await expect(page.locator("#passport-color")).toHaveText("D");
  await expect(page.locator("#passport-expert-cut")).toHaveText("Excellent");
  await expect(page.locator("#public-passport-card")).toContainText("Природний");
  await expect(page.locator("#public-passport-card")).not.toContainText("Initial observation");
});
