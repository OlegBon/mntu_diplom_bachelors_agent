import { expect, test } from "@playwright/test";

const dashboardResponse = {
  items: [
    {
      report_id: "DR-00042",
      status: "draft",
      report_date: "2026-09-15T10:00:00Z",
      created_at: "2026-09-15T10:00:00Z",
      updated_at: "2026-09-15T10:00:00Z",
      issued_at: null,
      expert_id: 2,
      issued_by_id: null,
      expert_comment: null,
      system_proportions_grade: 0,
      system_cut_grade: 0,
      calculation_rule_version: "idc-demo-v1",
      expert_proportions_grade: null,
      expert_cut_grade: null,
      expert_confirmed_at: null,
      price: "6931.00",
      stone: {
        stone_id: 42,
        shape: "Round",
        carat_weight: 1.25,
        color_grade: 0,
        clarity_grade: 0,
        measurements_length: 6.0,
        measurements_width: 6.0,
        measurements_depth: 3.8,
        table_percent: 58.0,
        depth_percent: 61.0,
        crown_angle: 34.5,
        pavilion_angle: 40.8,
        girdle_thickness: null,
        culet_size: null,
        polish_grade: 0,
        symmetry_grade: 0,
        fluorescence_grade: 0,
        origin: "natural",
        treatment_status: "not_assessed",
        identification_status: "preliminary",
        identification_method: null,
        identification_conclusion: null,
        market_status: "available",
        legacy_origin_code: null,
      },
    },
  ],
  total: 1,
  page: 1,
  page_size: 25,
  total_pages: 1,
};

test("dashboard renders the private report page and its row action menu", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 2, username: "expert_1", first_name: "Test", last_name: "Expert", role: "gemologist" } }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: [
    { category: "color", grade_value: 0, grade_label: "D" },
    { category: "clarity", grade_value: 0, grade_label: "FL" },
    { category: "cut", grade_value: 0, grade_label: "Excellent" },
  ] }));
  await page.route("**/reports?**", (route) => route.fulfill({ json: dashboardResponse }));

  await page.goto("/dashboard.html");

  await expect(page.getByRole("heading", { name: "Всі звіти" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "DR-00042", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Пояснення demo-ціни звіту DR-00042" }).click();
  await expect(page.getByText("diamonds_dataset.csv")).toBeVisible();
  await page.getByRole("button", { name: "Відкрити дії для звіту DR-00042" }).click();
  await expect(page.getByRole("button", { name: "Переглянути" })).toBeDisabled();

  await page.getByRole("button", { name: "Фільтри" }).click();
  await page.getByLabel("Стан звіту").selectOption("draft");
  await page.getByRole("button", { name: "Застосувати" }).click();
  await expect(page).toHaveURL(/report_status=draft/);
});
