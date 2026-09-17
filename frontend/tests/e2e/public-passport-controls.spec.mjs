import { expect, test } from "@playwright/test";

const reviewReport = {
  report_id: "DR-01001",
  status: "review",
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
  expert_proportions_grade: 0,
  expert_cut_grade: 0,
  expert_confirmed_at: "2026-09-16T09:00:00Z",
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

test("admin does not see QR or passport actions before a report is issued", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "admin");
    localStorage.setItem("role", "admin");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 1, username: "admin", role: "admin" } }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: [] }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/events", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/media", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001", (route) => route.fulfill({ json: reviewReport }));

  await page.goto("/report-detail.html?id=DR-01001");

  await expect(page.locator("#detail-passport")).toBeVisible();
  await expect(page.locator("#detail-passport-state")).toContainText("після видачі");
  await expect(page.locator("#detail-passport-qr")).toBeHidden();
  await expect(page.locator("#detail-passport-publish")).toBeHidden();
  await expect(page.locator("#detail-passport-reissue")).toBeHidden();
  await expect(page.locator("#detail-passport-revoke")).toBeHidden();
});
