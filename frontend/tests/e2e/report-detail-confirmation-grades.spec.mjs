import { expect, test } from "@playwright/test";

const draftReport = {
  report_id: "DR-01001",
  status: "draft",
  report_date: "2026-09-16T09:00:00Z",
  examination_date: "2026-09-16",
  created_at: "2026-09-16T09:00:00Z",
  updated_at: "2026-09-16T09:00:00Z",
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
  price: null,
  stone: {
    stone_id: 1, shape: "Round", carat_weight: "1.00", color_grade: 0, clarity_grade: 0,
    measurements_length: "6.00", measurements_width: "6.00", measurements_depth: "3.80",
    table_percent: "58.00", depth_percent: "61.00", crown_angle: "34.50", pavilion_angle: "40.80",
    girdle_thickness: null, culet_size: null, polish_grade: 0, symmetry_grade: 0, fluorescence_grade: 0,
    origin: "natural", treatment_status: "not_assessed", identification_status: "preliminary",
    identification_method: null, identification_conclusion: null, market_status: "not_for_sale", legacy_origin_code: null,
  },
};

test("expert selects proportions while final cut remains server-derived", async ({ page }) => {
  let updatedPayload;
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 2, username: "expert_1", role: "gemologist" } }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: [
    { category: "girdle_thickness", code: "medium", label: "Medium", sort_order: 1 },
    { category: "culet_size", code: "none", label: "None", sort_order: 1 },
  ] }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: [
    { category: "proportions", grade_value: 0, grade_label: "Excellent" },
    { category: "proportions", grade_value: 1, grade_label: "Very Good" },
    { category: "cut", grade_value: 0, grade_label: "Excellent" },
    { category: "cut", grade_value: 2, grade_label: "Good" },
    { category: "polish", grade_value: 0, grade_label: "Excellent" },
    { category: "polish", grade_value: 1, grade_label: "Very Good" },
    { category: "symmetry", grade_value: 0, grade_label: "Excellent" },
    { category: "symmetry", grade_value: 2, grade_label: "Good" },
  ] }));
  await page.route("**/reports/DR-01001/events", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/media", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001", async (route) => {
    if (route.request().method() === "PUT") updatedPayload = route.request().postDataJSON();
    await route.fulfill({ json: draftReport });
  });

  await page.goto("/report-detail.html?id=DR-01001&edit=1");

  await expect(page.locator("#detail-polish option")).toHaveText(["Оберіть оцінку", "Excellent", "Very Good"]);
  await expect(page.locator("#detail-symmetry option")).toHaveText(["Оберіть оцінку", "Excellent", "Good"]);
  await expect(page.locator("#detail-expert-proportions option")).toHaveText(["Не задано", "Excellent", "Very Good"]);
  await expect(page.locator("#detail-expert-cut")).toHaveCount(0);
  await expect(page.locator("#detail-expert-cut-result")).toHaveValue("—");
  await page.locator("#detail-polish").selectOption("1");
  await page.locator("#detail-symmetry").selectOption("2");
  await page.locator("#detail-expert-proportions").selectOption("1");
  await expect(page.locator("#detail-expert-cut-result")).toHaveValue("Good");
  await Promise.all([
    page.waitForRequest((request) => request.url().endsWith("/reports/DR-01001") && request.method() === "PUT"),
    page.locator("#detail-save").click(),
  ]);
  expect(updatedPayload.expert_proportions_grade).toBe(1);
  expect(updatedPayload).not.toHaveProperty("expert_cut_grade");
  expect(updatedPayload.stone.polish_grade).toBe(1);
  expect(updatedPayload.stone.symmetry_grade).toBe(2);
});
