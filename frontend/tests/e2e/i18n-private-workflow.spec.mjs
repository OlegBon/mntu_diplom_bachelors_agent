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

const detailReport = {
  report_id: "DR-00042", status: "draft", expert_id: 2, report_date: "2026-09-15T10:00:00Z", created_at: "2026-09-15T10:00:00Z",
  examination_date: "2026-09-15", expert_comment: "Initial comment", expert_proportions_grade: null, expert_cut_grade: null,
  system_proportions_grade: 0, system_cut_grade: 0,
  stone: {
    shape: "Round", carat_weight: 1.25, color_grade: 0, clarity_grade: 0, fluorescence_grade: 0,
    measurements_length: 6, measurements_width: 6, measurements_depth: 3.8, table_percent: 58, depth_percent: 61,
    crown_angle: 34.5, pavilion_angle: 40.8, girdle_thickness: "medium", culet_size: "none", polish_grade: 0,
    symmetry_grade: 0, origin: "natural", treatment_status: "not_assessed", identification_status: "preliminary",
    identification_method: "Microscope", identification_conclusion: "Natural diamond", market_status: "available",
  },
};

async function mockPrivateDetail(page) {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 2, username: "expert_1", role: "gemologist" } }));
  await page.route("**/market/mappings", (route) => route.fulfill({ json: mappings }));
  await page.route("**/reference-values", (route) => route.fulfill({ json: [
    { category: "girdle_thickness", code: "medium", label: "Medium" },
    { category: "culet_size", code: "none", label: "None" },
  ] }));
  await page.route("**/reports/DR-00042/events", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-00042/media", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-00042/narrative-quality", (route) => route.fulfill({ json: { warnings: [] } }));
  await page.route("**/reports/DR-00042/valuations", (route) => route.fulfill({ json: [] }));
  await page.route("**/reports/DR-00042/passport", (route) => route.fulfill({ json: { passport: null } }));
  await page.route("**/reports/DR-00042", (route) => route.fulfill({ json: detailReport }));
}

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

test("locale switch preserves unsaved private report edits", async ({ page }) => {
  await mockPrivateDetail(page);
  await page.goto("/report-detail.html?id=DR-00042&edit=1&source=locale-check#detail");
  await expect(page.locator("#detail-save")).toBeVisible();
  await page.locator("#detail-comment").fill("Unsaved expert note");

  await page.getByRole("button", { name: "Ukrainian" }).click();

  await expect(page.locator("html")).toHaveAttribute("lang", "uk");
  await expect(page.locator("#detail-comment")).toHaveValue("Unsaved expert note");
  await expect(page.locator("#detail-shape")).toHaveValue("Round");
  await expect(page.locator("#detail-save")).toBeVisible();
  await expect(page).toHaveURL(/id=DR-00042/);
  await expect(page).toHaveURL(/source=locale-check/);
  await expect(page).toHaveURL(/lang=uk/);
  await expect(page).toHaveURL(/#detail$/);
});
