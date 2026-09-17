import { expect, test } from "@playwright/test";

const expertStats = [{
  expert_id: 2,
  expert_username: "expert_1",
  first_name: "Іван",
  last_name: "Експерт",
  middle_name: null,
  is_active: true,
  total_reports: 5,
  draft_reports: 2,
  review_reports: 1,
  issued_reports: 2,
  void_reports: 0,
}];

const adminStats = {
  pending_review_count: 1,
  oldest_review_started_at: "2026-09-16T08:00:00Z",
  admins: [{
    admin_id: 1,
    admin_username: "admin",
    first_name: "Адмін",
    last_name: "Системний",
    middle_name: null,
    is_active: true,
    completed_reviews: 2,
    returned_to_draft: 1,
    issued_reports: 1,
    voided_reports: 0,
    avg_review_duration_seconds: 3900,
    median_review_duration_seconds: 3900,
    shortest_reviews: [{ report_id: "DR-00011", decision: "issued", duration_seconds: 1800, decided_at: "2026-09-16T09:00:00Z" }],
    longest_reviews: [{ report_id: "DR-00012", decision: "draft", duration_seconds: 6000, decided_at: "2026-09-16T10:00:00Z" }],
  }, {
    admin_id: 3,
    admin_username: "admin_2",
    first_name: "Друга",
    last_name: "Адміністраторка",
    middle_name: null,
    is_active: true,
    completed_reviews: 0,
    returned_to_draft: 0,
    issued_reports: 0,
    voided_reports: 0,
    avg_review_duration_seconds: null,
    median_review_duration_seconds: null,
    shortest_reviews: [],
    longest_reviews: [],
  }],
};

test("administrator sees operational analytics without a fake stone chart", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "admin");
    localStorage.setItem("role", "admin");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 1, username: "admin", role: "admin" } }));
  await page.route("**/statistics/expert-performance", (route) => route.fulfill({ json: expertStats }));
  await page.route("**/statistics/admin-review-performance", (route) => route.fulfill({ json: adminStats }));

  await page.goto("/ml-analysis.html");

  await expect(page.getByRole("heading", { name: "Експерти та звіти" })).toBeVisible();
  await expect(page.getByRole("cell", { name: /Експерт Іван/ })).toBeVisible();
  await page.getByRole("button", { name: /Експерт Іван/ }).click();
  await expect(page.getByRole("dialog")).toContainText("Три найшвидші та найдовші завершені звіти");
  await page.getByRole("button", { name: "Закрити" }).click();
  await page.getByRole("tab", { name: "Адміністратори" }).click();
  await expect(page.getByText("Тривалість етапу перевірки")).toBeVisible();
  await expect(page.getByText("Адміністраторка Друга")).toBeVisible();
  await expect(page.getByRole("link", { name: "DR-00011" })).toHaveAttribute("href", "/report-detail.html?id=DR-00011");
  await page.getByRole("tab", { name: "Камені" }).click();
  await expect(page.getByText(/не показуються умовні графіки/)).toBeVisible();
});
