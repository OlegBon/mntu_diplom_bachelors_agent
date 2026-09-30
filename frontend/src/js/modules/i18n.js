const LOCALE_STORAGE_KEY = "diamant_locale";
const DEFAULT_LOCALE = "en";
const SUPPORTED_LOCALES = ["en", "uk"];

const catalogs = {
  en: {
    "app.title": "Diamant ID",
    "brand.home": "Diamant ID home",
    "navigation.primary": "Primary navigation",
    "navigation.verifyPassport": "Verify passport",
    "navigation.signIn": "Sign in",
    "navigation.allReports": "All reports",
    "navigation.demo": "Demo",
    "navigation.experts": "Experts",
    "navigation.references": "References",
    "navigation.marketData": "Market data",
    "navigation.analytics": "Analytics",
    "navigation.profile": "Profile",
    "navigation.newReport": "New report",
    "auth.administrator": "Administrator",
    "auth.gemologist": "Gemologist",
    "auth.user": "User",
    "auth.signOut": "Sign out",
    "menu.open": "Open menu",
    "session.saved": "Your session is preserved. The API is temporarily unavailable.",
    "session.retry": "Try again",
    "footer.privacy": "Privacy policy",
    "footer.documentation": "Documentation",
    "locale.switcher": "Language",
    "locale.en": "English",
    "locale.uk": "Ukrainian",
    "landing.title": "Diamond identification and assessment",
    "landing.subtitle": "Reliable passport verification and expert diamond reports in one workspace.",
    "landing.verifyPassport": "Verify passport",
    "landing.signIn": "Sign in to work with reports",
    "landing.heroAlt": "Diamond held in gemological tweezers",
    "landing.passportTitle": "Verification you can trust",
    "landing.passportDescription": "A public passport opens from a direct link, a QR-code link, or a code on the report page. Enter only the code here; an internal report number is not used for this.",
    "landing.passportCode": "Public passport code",
    "landing.passportPlaceholder": "Enter the code from the report page",
    "landing.verify": "Verify",
    "landing.principles": "Diamant ID capabilities",
    "landing.expertReports": "Expert reports",
    "landing.expertReportsText": "Consistent recording of stone characteristics and assessment results.",
    "landing.dataControl": "Data control",
    "landing.dataControlText": "A clear distinction between an expert conclusion and a calculated system result.",
    "landing.passportVerification": "Passport verification",
    "landing.passportVerificationText": "A dedicated public route for issued reports after passport and QR issuance.",
    "login.title": "Sign in",
    "login.subtitle": "Please authenticate to continue",
    "login.username": "Username",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.error": "Sign-in failed: {message}",
    "passport.invalidInternalNumber": "An internal report number is not a public passport code.",
    "passport.invalidCode": "Enter the public passport code shown on the report page.",
  },
  uk: {
    "app.title": "Diamant ID",
    "brand.home": "Головна Diamant ID",
    "navigation.primary": "Основна навігація",
    "navigation.verifyPassport": "Перевірити паспорт",
    "navigation.signIn": "Увійти",
    "navigation.allReports": "Всі звіти",
    "navigation.demo": "Демо",
    "navigation.experts": "Експерти",
    "navigation.references": "Довідники",
    "navigation.marketData": "Ринкові дані",
    "navigation.analytics": "Аналітика",
    "navigation.profile": "Профіль",
    "navigation.newReport": "Новий звіт",
    "auth.administrator": "Адміністратор",
    "auth.gemologist": "Експерт",
    "auth.user": "Користувач",
    "auth.signOut": "Вийти",
    "menu.open": "Відкрити меню",
    "session.saved": "Сеанс збережено. API тимчасово недоступний.",
    "session.retry": "Спробувати знову",
    "footer.privacy": "Політика конфіденційності",
    "footer.documentation": "Документація",
    "locale.switcher": "Мова",
    "locale.en": "Англійська",
    "locale.uk": "Українська",
    "landing.title": "Ідентифікація та оцінювання діамантів",
    "landing.subtitle": "Надійна перевірка паспортів та експертні звіти про діаманти — в одному робочому середовищі.",
    "landing.verifyPassport": "Перевірити паспорт",
    "landing.signIn": "Увійти для роботи зі звітами",
    "landing.heroAlt": "Діамант у гемологічному пінцеті",
    "landing.passportTitle": "Перевірка, якій можна довіряти",
    "landing.passportDescription": "Публічний паспорт відкривається за прямим посиланням, посиланням із QR-коду або кодом зі сторінки звіту. Тут введіть лише код; внутрішній номер звіту для цього не використовується.",
    "landing.passportCode": "Код публічного паспорта",
    "landing.passportPlaceholder": "Введіть код зі сторінки звіту",
    "landing.verify": "Перевірити",
    "landing.principles": "Можливості Diamant ID",
    "landing.expertReports": "Експертні звіти",
    "landing.expertReportsText": "Послідовна фіксація характеристик каменю та результатів оцінювання.",
    "landing.dataControl": "Контроль даних",
    "landing.dataControlText": "Чітке розмежування експертного висновку й розрахункового результату системи.",
    "landing.passportVerification": "Перевірка паспорта",
    "landing.passportVerificationText": "Окремий публічний маршрут для виданих звітів — після реалізації паспорта й QR.",
    "login.title": "Вхід у систему",
    "login.subtitle": "Будь ласка, авторизуйтесь",
    "login.username": "Логін",
    "login.password": "Пароль",
    "login.submit": "Увійти",
    "login.error": "Помилка входу: {message}",
    "passport.invalidInternalNumber": "Внутрішній номер звіту не є кодом публічного паспорта.",
    "passport.invalidCode": "Введіть код публічного паспорта зі сторінки звіту.",
  },
};

let activeLocale = DEFAULT_LOCALE;

function normalizeLocale(value) {
  return SUPPORTED_LOCALES.includes(value) ? value : DEFAULT_LOCALE;
}

function interpolate(message, values) {
  return message.replace(/\{(\w+)\}/g, (_match, name) => String(values[name] ?? `{${name}}`));
}

export function validateCatalogs() {
  const englishKeys = Object.keys(catalogs.en).sort();
  for (const locale of SUPPORTED_LOCALES) {
    const localeKeys = Object.keys(catalogs[locale]).sort();
    if (englishKeys.length !== localeKeys.length || englishKeys.some((key, index) => key !== localeKeys[index])) {
      throw new Error(`i18n catalog keys do not match for locale ${locale}.`);
    }
    for (const key of localeKeys) {
      if (!catalogs[locale][key]?.trim()) throw new Error(`i18n catalog value is missing for ${locale}.${key}.`);
    }
  }
}

export function getLocale() {
  return activeLocale;
}

export function resolveLocale(search = globalThis.window?.location?.search ?? "", storedLocale = globalThis.localStorage?.getItem(LOCALE_STORAGE_KEY)) {
  const requestedLocale = new URLSearchParams(search).get("lang");
  if (SUPPORTED_LOCALES.includes(requestedLocale)) return requestedLocale;
  return normalizeLocale(storedLocale);
}

export function t(key, values = {}) {
  const message = catalogs[activeLocale]?.[key];
  if (!message) throw new Error(`Missing i18n key: ${key}`);
  return interpolate(message, values);
}

export function formatDate(value, options = {}) {
  return new Intl.DateTimeFormat(activeLocale === "uk" ? "uk-UA" : "en-US", options).format(value);
}

export function formatNumber(value, options = {}) {
  return new Intl.NumberFormat(activeLocale === "uk" ? "uk-UA" : "en-US", options).format(value);
}

export function formatCurrency(value, currency, options = {}) {
  return formatNumber(value, { style: "currency", currency, ...options });
}

export function applyTranslations(root = globalThis.document) {
  if (!root) return;
  root.documentElement?.setAttribute("lang", activeLocale);
  if (root.title !== undefined) root.title = t("app.title");
  root.querySelectorAll?.("[data-i18n]").forEach((node) => { node.textContent = t(node.dataset.i18n); });
  root.querySelectorAll?.("[data-i18n-placeholder]").forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  root.querySelectorAll?.("[data-i18n-alt]").forEach((node) => { node.alt = t(node.dataset.i18nAlt); });
  root.querySelectorAll?.("[data-i18n-aria-label]").forEach((node) => { node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel)); });
  root.querySelectorAll?.("[data-locale-switch]").forEach((node) => {
    const isActive = node.dataset.localeSwitch === activeLocale;
    node.setAttribute("aria-pressed", String(isActive));
    node.classList.toggle("is-active", isActive);
  });
}

export function setLocale(locale, { updateUrl = true } = {}) {
  activeLocale = normalizeLocale(locale);
  globalThis.localStorage?.setItem(LOCALE_STORAGE_KEY, activeLocale);
  if (updateUrl && globalThis.window?.location && globalThis.window?.history?.replaceState) {
    const url = new URL(globalThis.window.location.href);
    url.searchParams.set("lang", activeLocale);
    globalThis.window.history.replaceState(globalThis.window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
  }
  applyTranslations();
  const LocaleChangeEvent = globalThis.window?.CustomEvent ?? globalThis.CustomEvent;
  if (LocaleChangeEvent) globalThis.window?.dispatchEvent?.(new LocaleChangeEvent("diamant:locale-change", { detail: { locale: activeLocale } }));
  return activeLocale;
}

export function initializeI18n() {
  validateCatalogs();
  activeLocale = resolveLocale();
  applyTranslations();
  return activeLocale;
}

export const i18nCatalogs = catalogs;
