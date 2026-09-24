import { expect, test } from "@playwright/test";

const API_BASE_URL = "http://127.0.0.1:8010";

async function login(page, username, password) {
  await page.goto("/login.html");
  await page.locator("#username").fill(username);
  await page.locator("#password").fill(password);
  const [tokenResponse] = await Promise.all([
    page.waitForResponse((response) => response.url() === `${API_BASE_URL}/token`),
    page.locator("#login-form button[type=submit]").click(),
  ]);
  expect(tokenResponse.status()).toBe(200);
  await expect(page).toHaveURL(/\/$/);
  await expect.poll(() => page.evaluate(() => localStorage.getItem("token"))).not.toBeNull();
  await page.goto("/dashboard.html");
  await expect(page.locator("[data-dashboard]")).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript((apiBaseUrl) => { window.DIAMANT_API_BASE_URL = apiBaseUrl; }, API_BASE_URL);
});

test("real isolated API flow creates, issues and publishes a passport", async ({ page }) => {
  await login(page, "e2e-gemologist", "E2eGemologist123");
  await page.locator("#create-report-action").click();
  await expect(page).toHaveURL(/create-report\.html/);

  await page.locator("#shape").selectOption("Round");
  await page.locator("#origin").selectOption("natural");
  await page.locator("#carat-weight").fill("1.25");
  await page.locator("#color-grade").selectOption("0");
  await page.locator("#clarity-grade").selectOption("0");
  await page.locator("#next-btn").click();
  for (const [selector, value] of [
    ["#measurements-length", "6"], ["#measurements-width", "6"], ["#measurements-depth", "3.8"],
    ["#table-percent", "58"], ["#depth-percent", "61"], ["#crown-angle", "34.5"], ["#pavilion-angle", "40.8"],
  ]) await page.locator(selector).fill(value);
  await page.locator("#girdle-thickness").selectOption("medium");
  await page.locator("#culet-size").selectOption("none");
  await page.locator("#next-btn").click();
  await page.locator("#polish-grade").selectOption("0");
  await page.locator("#symmetry-grade").selectOption("0");
  await page.locator("#fluorescence-grade").selectOption("0");
  await page.locator("#treatment-status").selectOption("not_assessed");
  await page.locator("#identification-status").selectOption("preliminary");
  await page.locator("#save-btn").click();
  await expect(page).toHaveURL(/dashboard\.html\?created=DR-/);
  const reportUrl = await page.locator(".id-link").first().getAttribute("href");
  const reportId = new URL(reportUrl, page.url()).searchParams.get("id");
  expect(reportId).toBeTruthy();

  await page.goto(`/report-detail.html?id=${reportId}`);
  await page.locator("#detail-edit").click();
  await page.locator("#detail-expert-proportions").selectOption("0");
  await page.locator("#detail-save").click();
  await expect(page.locator("#detail-edit")).toBeVisible();
  await page.getByRole("button", { name: "Передати на перевірку" }).click();
  await expect(page.locator("#detail-status-badge")).toHaveText("На перевірці");
  await page.getByRole("button", { name: "Вийти" }).click();
  await login(page, "e2e-admin", "E2eAdmin123");
  await page.goto(`/report-detail.html?id=${reportId}`);
  await page.getByRole("button", { name: "Видати звіт" }).click();
  await expect(page.locator("#detail-status-badge")).toHaveText("Видано");
  await page.locator("#detail-passport-publish").click();
  await expect(page.locator("#detail-passport-code")).toBeVisible();
  const publicId = await page.locator("#detail-passport-code code").textContent();
  await expect(page.locator("#detail-passport-pdf")).toBeVisible();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#detail-passport-pdf").click(),
  ]);
  expect(download.suggestedFilename()).toBe(`passport-${reportId}.pdf`);
  await page.goto(`/passport.html?id=${publicId}`);
  await expect(page.locator("#public-passport-title")).toContainText(reportId);
});
