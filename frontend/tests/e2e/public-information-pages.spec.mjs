import { expect, test } from "@playwright/test";

test("public footer information pages render on desktop and mobile", async ({ page }) => {
  await page.goto("/privacy.html");
  await expect(page.getByRole("heading", { name: "Політика конфіденційності" })).toBeVisible();
  await expect(page.getByText("не фінальна юридична політика", { exact: false })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/documentation.html");
  await expect(page.getByRole("heading", { name: "Довідка з перевірки паспорта" })).toBeVisible();
  await expect(page.getByText("Три способи перевірки")).toBeVisible();
  await expect(page.locator(".footer-links a[href='/privacy.html']")).toBeVisible();
});
