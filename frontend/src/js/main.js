import { checkAuth, clearSession, isConfirmedUnauthorized, logout } from "./modules/auth.js";
import { getCurrentUser, loginUser } from "./modules/api.js";
import { initDashboard } from "./modules/dashboard.js";
import { initReportWizard } from "./modules/report-wizard.js";
import { initReportDetail } from "./modules/report-detail.js";
import { initPublicPassport } from "./modules/public-passport.js";
import { initProfile } from "./modules/profile.js";
import { initAdminUsers } from "./modules/admin-users.js";
import { initReferenceCatalog } from "./modules/reference-catalog.js";
import { initAnalytics } from "./modules/analytics.js";
import { initMarketData } from "./modules/market-data.js";
import { initPasswordVisibility } from "./modules/password-visibility.js";
import { initDemoReports } from "./modules/demo-reports.js";
import { initDemoReportDetail } from "./modules/demo-report-detail.js";
import { initializeI18n, setLocale, t } from "./modules/i18n.js";

function createNavigationLink(href, labelKey, className = "") {
  const item = document.createElement("li");
  if (className) item.className = className;
  const link = document.createElement("a");
  link.href = href;
  if (window.location.pathname === href) {
    link.classList.add("is-active");
    link.setAttribute("aria-current", "page");
  }
  link.textContent = t(labelKey);
  item.append(link);
  return item;
}

function publicPassportIdFromLookup(value) {
  if (/^DR-\d+/i.test(value)) {
    throw new Error(t("passport.invalidInternalNumber"));
  }
  if (/^[A-Za-z0-9_-]{20,128}$/.test(value)) return value;
  throw new Error(t("passport.invalidCode"));
}

function applyApprovedNavigation(isAuthenticated, user = null) {
  const navList = document.getElementById("nav-list");
  const authBlock = document.getElementById("auth-block");
  const sessionName = document.getElementById("header-session-name");
  if (!navList || !authBlock || !sessionName) return;

  navList.replaceChildren();
  authBlock.replaceChildren();
  navList.hidden = false;
  authBlock.hidden = false;
  if (!isAuthenticated) {
    navList.append(createNavigationLink("/#public-passport", "navigation.verifyPassport"));
    navList.append(createNavigationLink("/login.html", "navigation.signIn", "mobile-login"));
    const loginLink = document.createElement("a");
    loginLink.className = "header-session-action header-login";
    loginLink.href = "/login.html";
    loginLink.textContent = t("navigation.signIn");
    authBlock.append(loginLink);
    sessionName.hidden = true;
    return;
  }

  const username = user?.username || localStorage.getItem("username") || t("auth.user");
  const isAdmin = user?.role === "admin";
  const demoAccessEnabled = isAdmin && user?.demo_access_enabled === true;
  const createReportAction = document.getElementById("create-report-action");
  if (createReportAction) createReportAction.hidden = isAdmin;

  sessionName.replaceChildren();
  const sessionUsername = document.createElement("span");
  sessionUsername.className = "header-session-username";
  sessionUsername.textContent = username;
  const sessionRole = document.createElement("span");
  sessionRole.className = "header-session-role";
  sessionRole.textContent = isAdmin ? t("auth.administrator") : t("auth.gemologist");
  sessionName.append(sessionUsername, sessionRole);
  sessionName.hidden = false;

  const links = isAdmin
    ? [["/dashboard.html", "navigation.allReports"], ...(demoAccessEnabled ? [["/demo-reports.html", "navigation.demo"]] : []), ["/experts.html", "navigation.experts"], ["/references.html", "navigation.references"], ["/market-data.html", "navigation.marketData"], ["/ml-analysis.html", "navigation.analytics"], ["/profile.html", "navigation.profile"]]
    : [["/dashboard.html", "navigation.allReports"], ["/create-report.html", "navigation.newReport"], ["/profile.html", "navigation.profile"]];
  for (const [href, labelKey] of links) navList.append(createNavigationLink(href, labelKey));

  const mobileAccount = document.createElement("li");
  mobileAccount.className = "mobile-account";
  const accountName = document.createElement("span");
  accountName.className = "mobile-account-name";
  accountName.textContent = username;
  const accountRole = document.createElement("span");
  accountRole.className = "mobile-account-role";
  accountRole.textContent = isAdmin ? t("auth.administrator") : t("auth.gemologist");
  const mobileLogout = document.createElement("button");
  mobileLogout.type = "button";
  mobileLogout.className = "mobile-logout";
  mobileLogout.textContent = t("auth.signOut");
  mobileLogout.addEventListener("click", logout);
  mobileAccount.append(accountName, accountRole, mobileLogout);
  navList.append(mobileAccount);

  const logoutButton = document.createElement("button");
  logoutButton.type = "button";
  logoutButton.className = "header-session-action header-logout";
  logoutButton.textContent = t("auth.signOut");
  logoutButton.addEventListener("click", logout);
  authBlock.append(logoutButton);
}

function initializeAuthenticatedPage(currentPath, isCreateReportPage) {
  if (currentPath.endsWith("/dashboard.html")) void initDashboard();
  if (isCreateReportPage) void initReportWizard();
  if (currentPath.endsWith("/report-detail.html")) void initReportDetail();
  if (currentPath.endsWith("/profile.html")) void initProfile();
  if (currentPath.endsWith("/experts.html")) void initAdminUsers();
  if (currentPath.endsWith("/references.html")) void initReferenceCatalog();
  if (currentPath.endsWith("/market-data.html")) void initMarketData();
  if (currentPath.endsWith("/ml-analysis.html")) void initAnalytics();
  if (currentPath.endsWith("/demo-reports.html")) void initDemoReports();
  if (currentPath.endsWith("/demo-report-detail.html")) void initDemoReportDetail();
}

document.addEventListener("DOMContentLoaded", () => {
  initializeI18n();
  initPasswordVisibility();
  const isAuthenticated = checkAuth();
  const isAdmin = localStorage.getItem("role") === "admin";
  const currentPath = window.location.pathname;
  const isProtectedPage = ["/dashboard.html", "/create-report.html", "/report-detail.html", "/demo-reports.html", "/demo-report-detail.html", "/profile.html", "/experts.html", "/references.html", "/market-data.html", "/ml-analysis.html"].includes(currentPath);
  const isCreateReportPage = currentPath.endsWith("/create-report.html");

  if (!isAuthenticated && isProtectedPage) {
    window.location.replace("/login.html");
    return;
  }
  if (isAdmin && isCreateReportPage) {
    window.location.replace("/dashboard.html");
    return;
  }

  const protectedPage = document.querySelector("[data-protected-page]");
  const homeLoginCta = document.getElementById("home-login-cta");
  const retryState = document.getElementById("session-retry-state");
  const retryMessage = document.getElementById("session-retry-message");
  const retryButton = document.getElementById("session-retry-button");

  const hideRetryState = () => {
    if (retryState) retryState.hidden = true;
  };
  const showRetryState = () => {
    if (retryMessage) retryMessage.textContent = t("session.saved");
    if (retryState) retryState.hidden = false;
  };
  const bootstrapAuthenticatedSession = async () => {
    if (retryButton) retryButton.disabled = true;
    try {
      const user = await getCurrentUser(localStorage.getItem("token"));
      localStorage.setItem("username", user.username);
      localStorage.setItem("role", user.role);
      localStorage.setItem("demo_access_enabled", String(user.demo_access_enabled));
      if (currentPath.startsWith("/demo-") && !user.demo_access_enabled) {
        window.location.replace("/dashboard.html");
        return;
      }
      if (protectedPage) protectedPage.hidden = false;
      if (homeLoginCta) homeLoginCta.hidden = true;
      hideRetryState();
      applyApprovedNavigation(true, user);
      initializeAuthenticatedPage(currentPath, isCreateReportPage);
    } catch (error) {
      if (isConfirmedUnauthorized(error)) {
        clearSession();
        window.location.replace("/login.html");
        return;
      }
      showRetryState();
    } finally {
      if (retryButton) retryButton.disabled = false;
    }
  };
  if (!isAuthenticated) {
    if (protectedPage) protectedPage.hidden = false;
    if (homeLoginCta) {
      homeLoginCta.hidden = false;
      homeLoginCta.classList.remove("home-login-cta--pending");
    }
    applyApprovedNavigation(false);
  }

  if (isAuthenticated) {
    void bootstrapAuthenticatedSession();
    retryButton?.addEventListener("click", () => void bootstrapAuthenticatedSession());
  }

  document.querySelectorAll("[data-locale-switch]").forEach((button) => {
    button.addEventListener("click", () => setLocale(button.dataset.localeSwitch));
  });
  window.addEventListener("diamant:locale-change", () => {
    applyApprovedNavigation(isAuthenticated, isAuthenticated ? {
      username: localStorage.getItem("username"),
      role: localStorage.getItem("role"),
      demo_access_enabled: localStorage.getItem("demo_access_enabled") === "true",
    } : null);
  });

  window.addEventListener("demo-access-changed", (event) => {
    const user = event.detail;
    applyApprovedNavigation(true, user);
  });

  if (currentPath.endsWith("/passport.html")) void initPublicPassport();

  const burgerBtn = document.getElementById("burger-btn");
  const mainNav = document.getElementById("main-nav");
  if (burgerBtn && mainNav) {
    const closeNavigationDrawer = () => {
      burgerBtn.classList.remove("is-active");
      mainNav.classList.remove("is-active");
      burgerBtn.setAttribute("aria-expanded", "false");
    };
    burgerBtn.addEventListener("click", () => {
      burgerBtn.classList.toggle("is-active");
      mainNav.classList.toggle("is-active");
      burgerBtn.setAttribute("aria-expanded", String(mainNav.classList.contains("is-active")));
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 900) closeNavigationDrawer();
    });
  }

  if (currentPath.includes("login.html")) {
    if (isAuthenticated) window.location.href = "/";
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errorMessage = document.getElementById("error-msg");
        try {
          const token = await loginUser(loginForm.username.value, loginForm.password.value);
          localStorage.setItem("token", token);
          localStorage.setItem("username", loginForm.username.value);
          localStorage.removeItem("role");
          window.location.href = "/";
        } catch (error) {
          errorMessage.textContent = t("login.error", { message: error.message });
          errorMessage.style.display = "block";
        }
      });
    }
  }

  const searchForm = document.getElementById("public-search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const input = document.getElementById("search-input");
      const status = document.getElementById("public-search-status");
      try {
        const publicId = publicPassportIdFromLookup(input.value.trim());
        window.location.href = `/passport.html?id=${encodeURIComponent(publicId)}`;
      } catch (error) {
        status.textContent = error.message;
        status.hidden = false;
      }
    });
  }
});
