import { expect, test } from "@playwright/test";

test("password visibility control changes both field and visible control state", async ({ page }) => {
  await page.goto("/login.html");

  const input = page.locator("#password");
  const toggle = page.getByRole("button", { name: "Показати пароль" });
  await expect(input).toHaveAttribute("type", "password");
  await expect(toggle).toHaveAttribute("aria-pressed", "false");

  await toggle.click();
  await expect(input).toHaveAttribute("type", "text");
  await expect(page.getByRole("button", { name: "Сховати пароль" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".password-control__toggle")).toHaveClass(/is-visible/);

  await page.getByRole("button", { name: "Сховати пароль" }).click();
  await expect(input).toHaveAttribute("type", "password");
  await expect(page.getByRole("button", { name: "Показати пароль" })).toHaveAttribute("aria-pressed", "false");
});
