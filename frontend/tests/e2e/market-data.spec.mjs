import { expect, test } from "@playwright/test";

const provider = {
  provider_code: "openfacet", display_name: "OpenFacet", provider_type: "market_reference",
  documentation_url: "https://openfacet.net/en/api-docs/", terms_url: "https://openfacet.net/en/terms/",
  scope_note: "Comparable natural GIA reference only.", is_active: true,
};

const nbuProvider = {
  provider_code: "nbu", display_name: "НБУ", provider_type: "fx_reference",
  documentation_url: "https://bank.gov.ua/ua/markets/exchangerates", terms_url: "https://bank.gov.ua/ua/about/terms-of-use",
  scope_note: "Official USD/UAH rate.", is_active: true,
};

const candidate = {
  snapshot_id: 17, provider_code: "openfacet", snapshot_kind: "market_reference", status: "candidate",
  currency_code: "USD", unit: "USD_PER_CARAT", source_url: "https://data.openfacet.net/list_round.csv",
  methodology_url: "https://openfacet.net/en/methodology/", coverage_note: "Comparable natural GIA reference only.",
  quote_count: 1, content_sha256: "a".repeat(64), retrieved_at: "2026-09-17T12:00:00Z",
  created_by_id: 1, approved_by_id: null, approved_at: null, decision_reason: null, created_at: "2026-09-17T12:00:00Z",
};

let policy = {
  policy_id: 1, market_provider_code: "openfacet", use_fx_conversion: true,
  fx_provider_code: "nbu", updated_by_id: 1, updated_at: "2026-09-17T12:00:00Z",
};

const schedules = [
  { provider_code: "openfacet", enabled: true, timezone_name: "Europe/Kyiv", scheduled_hour: 8, scheduled_minute: 30, warn_after_hours: 168, block_after_hours: 336, updated_by_id: null, updated_at: "2026-09-24T08:00:00Z", freshness_status: "fresh", latest_retrieved_at: "2026-09-24T08:30:00Z" },
  { provider_code: "nbu", enabled: true, timezone_name: "Europe/Kyiv", scheduled_hour: 15, scheduled_minute: 40, warn_after_hours: 36, block_after_hours: 72, updated_by_id: null, updated_at: "2026-09-24T08:00:00Z", freshness_status: "missing", latest_retrieved_at: null },
];

test("administrator creates and approves a market-data candidate before using it", async ({ page }) => {
  let snapshots = [];
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-token");
    localStorage.setItem("username", "admin");
    localStorage.setItem("role", "admin");
  });
  await page.route("**/users/me", (route) => route.fulfill({ json: { expert_id: 1, username: "admin", role: "admin" } }));
  await page.route("**/market-data/providers", (route) => route.fulfill({ json: [nbuProvider, provider] }));
  await page.route("**/market-data/policy", async (route) => {
    if (route.request().method() === "PUT") policy = { ...policy, ...(route.request().postDataJSON() || {}) };
    await route.fulfill({ json: policy });
  });
  await page.route("**/market-data/snapshots", (route) => route.fulfill({ json: snapshots }));
  await page.route("**/market-data/fx-snapshots", (route) => route.fulfill({ json: [] }));
  await page.route("**/market-data/provider-schedules**", async (route) => {
    if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON();
      const item = schedules.find((schedule) => schedule.provider_code === body.provider_code);
      Object.assign(item, body);
      await route.fulfill({ json: item });
      return;
    }
    await route.fulfill({ json: schedules });
  });
  await page.route("**/market-data/operations", (route) => route.fulfill({ json: [] }));
  await page.route("**/market-data/providers/openfacet/fetch", (route) => {
    snapshots = [candidate];
    return route.fulfill({ json: candidate });
  });
  await page.route("**/market-data/snapshots/17/approve", (route) => {
    snapshots = [{ ...candidate, status: "approved", approved_by_id: 1, approved_at: "2026-09-17T12:01:00Z" }];
    return route.fulfill({ json: snapshots[0] });
  });

  await page.goto("/market-data.html");
  await expect(page.locator("[data-market-data-page]")).toBeVisible();
  await expect(page.locator("#market-data-providers")).toContainText("OpenFacet");
  await expect(page.locator("#market-reference-policy-form")).toContainText("OpenFacet");
  await expect(page.locator("#market-provider-schedules")).toContainText("Увімкнути планове оновлення");
  const scheduleForm = page.locator("#market-provider-schedules form").first();
  await scheduleForm.getByLabel("Час (Europe/Kyiv)").fill("09:00");
  await scheduleForm.getByRole("button", { name: "Зберегти графік" }).click();
  await expect(page.locator("#market-data-status")).toContainText("Графік оновлення збережено");
  await page.getByRole("button", { name: "Отримати кандидат" }).click();
  await expect(page.locator("#market-data-snapshots")).toContainText("Кандидат");
  await page.getByRole("button", { name: "Затвердити" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByLabel("Коментар до затвердження").fill("Перевірено");
  await page.getByRole("button", { name: "Затвердити знімок" }).click();
  await expect(page.locator("#market-reference-snapshot")).toBeEnabled();
  await expect(page.locator("#market-data-snapshots")).toContainText("Затверджено");
});
