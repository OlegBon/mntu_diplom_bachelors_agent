import { expect, test } from "@playwright/test";

test("login page renders its form", async ({ page }) => {
  await page.goto("/login.html");

  await expect(page.locator("#login-form")).toBeVisible();
  await expect(page.locator("#username")).toHaveAttribute("autocomplete", "username");
  await expect(page.locator("#password")).toHaveAttribute("autocomplete", "current-password");
});

test("tablet navigation opens and closes from the burger control", async ({ page }) => {
  await page.setViewportSize({ width: 800, height: 900 });
  await page.goto("/");

  const navigation = page.locator("#main-nav");
  const burger = page.locator("#burger-btn");
  await expect(navigation).toBeHidden();
  await burger.click();
  await expect(navigation).toBeVisible();
  await burger.click();
  await expect(navigation).toBeHidden();
});
