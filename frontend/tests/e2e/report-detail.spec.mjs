import { expect, test } from "@playwright/test";

const report = {
  report_id: "DR-01001",
  status: "draft",
  report_date: "2026-09-16T09:00:00Z",
  examination_date: "2026-09-16",
  created_at: "2026-09-16T09:00:00Z",
  updated_at: "2026-09-16T09:00:00Z",
  issued_at: null,
  expert_id: 2,
  issued_by_id: null,
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
    origin: "natural", treatment_status: "not_assessed", identification_status: "preliminary",
    identification_method: null, identification_conclusion: null, market_status: "not_for_sale", legacy_origin_code: null,
  },
};

const valuations = [
  {
    valuation_id: 2, stone_id: 1, valuation_kind: "system_market_reference", amount: "62782.00", currency_code: "USD", unit: "TOTAL_STONE",
    source_name: "OpenFacet", source_reference: "snapshot:1", market_snapshot_id: 1, applicability_note: null,
    fx_snapshot_id: 6, fx_rate: "44.66480000", fx_rate_date: "2026-09-18", converted_amount: "2804145.47", converted_currency_code: "UAH",
    observed_at: "2026-09-17T13:18:00Z", created_by_id: 2, created_at: "2026-09-18T09:00:00Z",
  },
  {
    valuation_id: 1, stone_id: 1, valuation_kind: "system_market_reference", amount: "11668.00", currency_code: "USD", unit: "TOTAL_STONE",
    source_name: "OpenFacet", source_reference: "snapshot:1", market_snapshot_id: 1, applicability_note: null,
    fx_snapshot_id: 5, fx_rate: "44.66480000", fx_rate_date: "2026-09-18", converted_amount: "521148.89", converted_currency_code: "UAH",
    observed_at: "2026-09-17T13:18:00Z", created_by_id: 2, created_at: "2026-09-17T15:00:00Z",
  },
];

test("owner edits a draft and sees the recorded private history", async ({ page }) => {
  let updatedPayload;
  const workSessionActions = [];
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
    { category: "color", grade_value: 0, grade_label: "D" },
    { category: "clarity", grade_value: 0, grade_label: "FL" },
    { category: "fluorescence", grade_value: 0, grade_label: "None" },
    { category: "polish", grade_value: 0, grade_label: "Excellent" },
    { category: "symmetry", grade_value: 0, grade_label: "Excellent" },
    { category: "proportions", grade_value: 0, grade_label: "Excellent" },
    { category: "cut", grade_value: 0, grade_label: "Excellent" },
  ] }));
  await page.route("**/reports/DR-01001/events", (route) => route.fulfill({ json: [
    { event_id: 1, action: "created", from_status: null, to_status: "draft", actor_id: 2, reason: null, created_at: "2026-09-16T09:00:00Z" },
    { event_id: 2, action: "report_updated", from_status: "draft", to_status: "draft", actor_id: 2, reason: null, created_at: "2026-09-16T09:05:00Z" },
    { event_id: 3, action: "system_market_reference_added", from_status: null, to_status: null, actor_id: 2, reason: "USD 11,668.00 · OpenFacet · знімок #1", created_at: "2026-09-17T15:00:00Z" },
    { event_id: 4, action: "market_reference_added", from_status: null, to_status: null, actor_id: 1, reason: "USD 62,782.00 · OpenFacet · знімок #1", created_at: "2026-09-18T09:00:00Z" },
  ] }));
  await page.route("**/reports/DR-01001/media", (route) => route.fulfill({ json: [
    {
      media_id: 7, report_id: "DR-01001", asset_type: "stone_photo", original_filename: "stone.png",
      mime_type: "image/png", size_bytes: 10, sha256: "a".repeat(64), uploaded_by_id: 2,
      created_at: "2026-09-16T09:00:00Z", is_public: false,
    },
  ] }));
  await page.route("**/reports/DR-01001/media/7/content", (route) => route.fulfill({
    contentType: "image/png", body: "image-placeholder",
  }));
  await page.route("**/reports/DR-01001/valuations", (route) => route.fulfill({ json: valuations }));
  await page.route("**/reports/DR-01001/work-session", async (route) => {
    const payload = route.request().postDataJSON();
    workSessionActions.push(payload.action);
    await route.fulfill({ json: { work_session_id: "session-1", active_seconds: 10, is_active: payload.action !== "pause" } });
  });
  await page.route("**/reports/DR-01001", async (route) => {
    if (route.request().method() === "PUT") updatedPayload = route.request().postDataJSON();
    await route.fulfill({ json: report });
  });

  await page.goto("/report-detail.html?id=DR-01001&edit=1");
  await expect(page.locator("#report-detail-title")).toHaveText("DR-01001");
  await expect(page.locator("#detail-status-badge")).toHaveText("Чернетка");
  await expect(page.locator("#detail-events")).toContainText("Дані чернетки оновлено");
  await expect(page.locator("#detail-events")).toContainText("Системний довідковий орієнтир додано");
  await expect(page.locator("#detail-events")).toContainText("Довідковий орієнтир підтверджено адміністратором");
  await expect(page.locator("#detail-media")).toContainText("stone.png");
  await expect(page.locator("#detail-transitions")).toContainText("Передати на перевірку");
  const valuationDisclosures = page.locator("#detail-valuations details");
  await expect(valuationDisclosures).toHaveCount(2);
  await expect(valuationDisclosures.nth(0)).toHaveAttribute("open", "");
  await expect(valuationDisclosures.nth(1)).not.toHaveAttribute("open", "");
  await valuationDisclosures.nth(1).locator("summary").click();
  await expect(valuationDisclosures.nth(1)).toHaveAttribute("open", "");
  await page.locator("#detail-comment").fill("Updated observation");
  await Promise.all([
    page.waitForResponse((response) => response.url().endsWith("/reports/DR-01001") && response.request().method() === "PUT"),
    page.locator("#detail-save").click(),
  ]);
  expect(updatedPayload.expert_comment).toBe("Updated observation");
  expect(updatedPayload.stone.market_status).toBe("not_for_sale");
  expect(workSessionActions).toContain("start");
  expect(workSessionActions).toContain("save");
});

test("admin confirms passport-media publication in a project dialog", async ({ page }) => {
  const issuedReport = { ...report, status: "issued", issued_at: "2026-09-18T09:00:00Z", issued_by_id: 1 };
  const publicationRequests = [];
  await page.addInitScript(() => {
    localStorage.setItem("token", "admin-e2e-token");
    localStorage.setItem("username", "admin");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 1, username: "admin", role: "admin" } }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: [] }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/events", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/valuations", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-01001/passport", (route) => route.fulfill({
    status: 404, contentType: "application/json", body: JSON.stringify({ detail: "Паспорт не опубліковано" }),
  }));
  await page.route("**/reports/DR-01001/media/7/publication", async (route) => {
    publicationRequests.push(route.request().postDataJSON());
    await route.fulfill({ json: { media_id: 7, is_public: true } });
  });
  await page.route("**/reports/DR-01001/media", (route) => route.fulfill({ json: [
    {
      media_id: 7, report_id: "DR-01001", asset_type: "stone_photo", original_filename: "stone.png",
      mime_type: "image/png", size_bytes: 10, sha256: "a".repeat(64), uploaded_by_id: 1,
      created_at: "2026-09-16T09:00:00Z", is_public: false,
    },
  ] }));
  await page.route("**/reports/DR-01001/media/7/content", (route) => route.fulfill({
    contentType: "image/png", body: "image-placeholder",
  }));
  await page.route("**/reports/DR-01001", (route) => route.fulfill({ json: issuedReport }));

  await page.goto("/report-detail.html?id=DR-01001");
  await page.getByRole("button", { name: "Опублікувати в паспорті" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("чинним посиланням або QR-кодом");
  await dialog.getByRole("button", { name: "Опублікувати в паспорті" }).click();
  await expect.poll(() => publicationRequests).toEqual([{ is_public: true }]);
  await expect(dialog).not.toBeVisible();
});
