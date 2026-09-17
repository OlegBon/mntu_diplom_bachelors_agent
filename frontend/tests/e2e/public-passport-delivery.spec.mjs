import { expect, test } from "@playwright/test";

const issuedReport = {
  report_id: "DR-01001",
  status: "issued",
  report_date: "2026-09-16T09:00:00Z",
  examination_date: "2026-09-15",
  created_at: "2026-09-16T09:00:00Z",
  updated_at: "2026-09-16T09:00:00Z",
  issued_at: "2026-09-16T09:00:00Z",
  expert_id: 2,
  issued_by_id: 1,
  expert_comment: "Initial observation",
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
    origin: "natural", treatment_status: "none_detected", identification_status: "confirmed",
    identification_method: null, identification_conclusion: null, market_status: "not_for_sale", legacy_origin_code: null,
  },
};

const publicId = "7-b_UhqTIn7HSWwgbyfHQqE27VtB-lew";

test("admin sees the public code and downloads a PDF passport", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "admin");
    localStorage.setItem("role", "admin");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 1, username: "admin", role: "admin" } }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: [] }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: [
    { category: "color", grade_value: 0, grade_label: "D" },
    { category: "clarity", grade_value: 0, grade_label: "FL" },
    { category: "proportions", grade_value: 0, grade_label: "Excellent" },
    { category: "cut", grade_value: 0, grade_label: "Excellent" },
  ] }));
  await page.route("**/reports/DR-01001/events", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/media", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/passport/qr?*", (route) => route.fulfill({ contentType: "image/svg+xml", body: "<svg></svg>" }));
  await page.route("**/reports/DR-01001/passport/pdf?*", (route) => route.fulfill({ contentType: "application/pdf", body: "%PDF-1.4" }));
  await page.route("**/reports/DR-01001/passport", (route) => route.fulfill({ json: { public_id: publicId, report_id: "DR-01001", is_active: true, created_at: "2026-09-16T09:00:00Z", revoked_at: null } }));
  await page.route("**/reports/DR-01001", (route) => {
    if (new URL(route.request().url()).pathname === "/reports/DR-01001") {
      return route.fulfill({ json: issuedReport });
    }
    return route.fallback();
  });

  await page.goto("/report-detail.html?id=DR-01001");

  await expect(page.locator("#detail-passport-code")).toContainText(publicId);
  await expect(page.locator("#detail-passport-copy-link")).toBeVisible();
  await expect(page.locator("#detail-passport-copy-code")).toBeVisible();
  await expect(page.locator("#detail-passport-pdf")).toBeVisible();
  const download = page.waitForEvent("download");
  await page.locator("#detail-passport-pdf").click();
  expect((await download).suggestedFilename()).toBe("passport-DR-01001.pdf");
});

test("public lookup accepts only a public code and rejects URL or an internal report number", async ({ page }) => {
  await page.route("**/public/passports/**", (route) => route.fulfill({ status: 404, json: { detail: "Passport not found" } }));
  await page.goto("/");

  await page.locator("#search-input").fill(publicId);
  await page.locator("#public-search-form button").click();
  await expect(page).toHaveURL(new RegExp(`passport\\.html\\?id=${publicId}`));

  await page.goto("/");
  await page.locator("#search-input").fill(`http://localhost:3000/passport.html?id=${publicId}`);
  await page.locator("#public-search-form button").click();
  await expect(page.locator("#public-search-status")).toContainText("код публічного паспорта");

  await page.locator("#search-input").fill("DR-01001");
  await page.locator("#public-search-form button").click();
  await expect(page.locator("#public-search-status")).toContainText("Внутрішній номер звіту");
});
