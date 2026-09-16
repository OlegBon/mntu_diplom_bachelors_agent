import { expect, test } from "@playwright/test";

const expert = {
  expert_id: 2,
  username: "expert_1",
  first_name: "Test",
  last_name: "Expert",
  middle_name: null,
  role: "gemologist",
  is_active: true,
};

test("profile renders immutable account metadata and saves own name", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "expert_1");
    localStorage.setItem("role", "gemologist");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: expert }));
  await page.route("**/users/me/profile", (route) => route.fulfill({ json: { ...expert, first_name: "Updated" } }));
  await page.goto("/profile.html");
  await expect(page.getByRole("heading", { name: "Профіль" })).toBeVisible();
  await expect(page.locator("#profile-username")).toBeDisabled();
  await page.locator("#profile-first-name").fill("Updated");
  await page.getByRole("button", { name: "Зберегти дані" }).click();
  await expect(page.getByText("Дані профілю збережено.")).toBeVisible();
});

test("admin can open account management without a fake reference editor", async ({ page }) => {
  const admin = { ...expert, expert_id: 1, username: "admin", role: "admin" };
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "admin");
    localStorage.setItem("role", "admin");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: admin }));
  await page.route("**/users/?**", (route) => route.fulfill({ json: { items: [admin, expert], total: 2, page: 1, page_size: 10, total_pages: 1 } }));
  await page.goto("/experts.html");
  await expect(page.getByRole("heading", { name: "Експерти" })).toBeVisible();
  await expect(page.getByRole("row", { name: /expert_1/ }).getByRole("button", { name: "Деактивувати" })).toBeVisible();
  await page.route("**/reference-values", (route) => route.fulfill({ json: [
    { category: "shape", code: "round", label: "Round", sort_order: 1 },
  ] }));
  await page.goto("/references.html");
  await expect(page.getByText("Поточні дані лише для перегляду.")).toBeVisible();
  await expect(page.getByRole("cell", { name: "Round", exact: true })).toBeVisible();
});
