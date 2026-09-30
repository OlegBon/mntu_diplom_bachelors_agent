import assert from "node:assert/strict";
import test from "node:test";
import { JSDOM } from "jsdom";

import {
  applyTranslations,
  formatCurrency,
  getLocale,
  initializeI18n,
  resolveLocale,
  setLocale,
  t,
  validateCatalogs,
} from "../src/js/modules/i18n.js";

function installDocument(url = "http://localhost/index.html?report_id=DR-00042#public-passport") {
  const dom = new JSDOM(`<!doctype html><html lang="en"><head><title>Diamant ID</title></head><body>
    <h1 data-i18n="landing.title">Diamond identification and assessment</h1>
    <input data-i18n-placeholder="landing.passportPlaceholder" />
    <button data-locale-switch="en"></button><button data-locale-switch="uk"></button>
  </body></html>`, { url });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  globalThis.localStorage = dom.window.localStorage;
  return dom;
}

test("i18n catalogs have complete matching release keys", () => {
  assert.doesNotThrow(() => validateCatalogs());
});

test("locale resolution honors URL, then saved preference, then English default", () => {
  assert.equal(resolveLocale("?lang=uk", "en"), "uk");
  assert.equal(resolveLocale("?lang=invalid", "uk"), "uk");
  assert.equal(resolveLocale("", null), "en");
});

test("locale switch translates DOM and preserves route, query state and hash", () => {
  installDocument();
  initializeI18n();
  assert.equal(getLocale(), "en");
  assert.equal(document.documentElement.lang, "en");

  setLocale("uk");

  assert.equal(getLocale(), "uk");
  assert.equal(document.documentElement.lang, "uk");
  assert.equal(document.querySelector("h1").textContent, "Ідентифікація та оцінювання діамантів");
  assert.equal(document.querySelector("input").placeholder, "Введіть код зі сторінки звіту");
  assert.equal(window.location.pathname, "/index.html");
  assert.equal(new URLSearchParams(window.location.search).get("report_id"), "DR-00042");
  assert.equal(new URLSearchParams(window.location.search).get("lang"), "uk");
  assert.equal(window.location.hash, "#public-passport");
  assert.equal(localStorage.getItem("diamant_locale"), "uk");
});

test("translation and currency formatting follow the active locale", () => {
  installDocument();
  initializeI18n();
  setLocale("en", { updateUrl: false });
  assert.equal(t("navigation.signIn"), "Sign in");
  assert.match(formatCurrency(1234.5, "USD"), /\$1,234\.50/);

  setLocale("uk", { updateUrl: false });
  applyTranslations();
  assert.equal(t("navigation.signIn"), "Увійти");
  assert.match(formatCurrency(1234.5, "USD"), /1[\s\u00a0]234,50/);
});
