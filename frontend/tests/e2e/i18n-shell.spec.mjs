import { expect, test } from "@playwright/test";

test("locale switch keeps public lookup input and URL state while translating the shared shell", async ({ page }) => {
  await page.goto("/?report_id=DR-00042#public-passport");

  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { name: "Diamond identification and assessment" })).toBeVisible();
  await page.getByLabel("Public passport code").fill("passport-code-123");

  await page.getByRole("button", { name: "Ukrainian" }).click();

  await expect(page.locator("html")).toHaveAttribute("lang", "uk");
  await expect(page.getByRole("heading", { name: "Ідентифікація та оцінювання діамантів" })).toBeVisible();
  await expect(page.getByLabel("Код публічного паспорта")).toHaveValue("passport-code-123");
  await expect(page).toHaveURL(/report_id=DR-00042/);
  await expect(page).toHaveURL(/lang=uk/);
  await expect(page).toHaveURL(/#public-passport$/);
});
