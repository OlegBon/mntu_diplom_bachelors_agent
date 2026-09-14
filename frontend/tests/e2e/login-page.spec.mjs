import { expect, test } from "@playwright/test";

test("login page renders its form", async ({ page }) => {
  await page.goto("/login.html");

  await expect(page.locator("#login-form")).toBeVisible();
  await expect(page.locator("#username")).toHaveAttribute("autocomplete", "username");
  await expect(page.locator("#password")).toHaveAttribute("autocomplete", "current-password");
});
