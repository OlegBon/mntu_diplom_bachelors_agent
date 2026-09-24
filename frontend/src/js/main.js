import { checkAuth, logout } from "./modules/auth.js";
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

function createNavigationLink(href, label, className = "") {
  const item = document.createElement("li");
  if (className) item.className = className;
  const link = document.createElement("a");
  link.href = href;
  link.textContent = label;
  item.append(link);
  return item;
}

function publicPassportIdFromLookup(value) {
  if (/^DR-\d+/i.test(value)) {
    throw new Error("Внутрішній номер звіту не є кодом публічного паспорта.");
  }
  if (/^[A-Za-z0-9_-]{20,128}$/.test(value)) return value;
  throw new Error("Введіть код публічного паспорта зі сторінки звіту.");
}

function applyApprovedNavigation(isAuthenticated) {
  const navList = document.getElementById("nav-list");
  const authBlock = document.getElementById("auth-block");
  const sessionName = document.getElementById("header-session-name");
  if (!navList || !authBlock || !sessionName) return;

  navList.replaceChildren();
  authBlock.replaceChildren();
  if (!isAuthenticated) {
    navList.append(createNavigationLink("/#public-passport", "Перевірити паспорт"));
    navList.append(createNavigationLink("/login.html", "Увійти", "mobile-login"));
    const loginLink = document.createElement("a");
    loginLink.className = "header-session-action header-login";
    loginLink.href = "/login.html";
    loginLink.textContent = "Увійти";
    authBlock.append(loginLink);
    sessionName.hidden = true;
    return;
  }

  const username = localStorage.getItem("username") || "Користувач";
  const isAdmin = localStorage.getItem("role") === "admin";
  const createReportAction = document.getElementById("create-report-action");
  if (createReportAction) createReportAction.hidden = isAdmin;

  sessionName.replaceChildren();
  const sessionUsername = document.createElement("span");
  sessionUsername.className = "header-session-username";
  sessionUsername.textContent = username;
  const sessionRole = document.createElement("span");
  sessionRole.className = "header-session-role";
  sessionRole.textContent = isAdmin ? "Адміністратор" : "Експерт";
  sessionName.append(sessionUsername, sessionRole);
  sessionName.hidden = false;

  const links = isAdmin
    ? [["/dashboard.html", "Всі звіти"], ["/experts.html", "Експерти"], ["/references.html", "Довідники"], ["/market-data.html", "Ринкові дані"], ["/ml-analysis.html", "Аналітика"], ["/profile.html", "Профіль"]]
    : [["/dashboard.html", "Всі звіти"], ["/create-report.html", "Новий звіт"], ["/profile.html", "Профіль"]];
  for (const [href, label] of links) navList.append(createNavigationLink(href, label));

  const mobileAccount = document.createElement("li");
  mobileAccount.className = "mobile-account";
  const accountName = document.createElement("span");
  accountName.className = "mobile-account-name";
  accountName.textContent = username;
  const accountRole = document.createElement("span");
  accountRole.className = "mobile-account-role";
  accountRole.textContent = isAdmin ? "Адміністратор" : "Експерт";
  const mobileLogout = document.createElement("button");
  mobileLogout.type = "button";
  mobileLogout.className = "mobile-logout";
  mobileLogout.textContent = "Вийти";
  mobileLogout.addEventListener("click", logout);
  mobileAccount.append(accountName, accountRole, mobileLogout);
  navList.append(mobileAccount);

  const logoutButton = document.createElement("button");
  logoutButton.type = "button";
  logoutButton.className = "header-session-action header-logout";
  logoutButton.textContent = "Вийти";
  logoutButton.addEventListener("click", logout);
  authBlock.append(logoutButton);
}

document.addEventListener("DOMContentLoaded", () => {
  initPasswordVisibility();
  const isAuthenticated = checkAuth();
  const isAdmin = localStorage.getItem("role") === "admin";
  const currentPath = window.location.pathname;
  const isProtectedPage = ["/dashboard.html", "/create-report.html", "/report-detail.html", "/profile.html", "/experts.html", "/references.html", "/market-data.html", "/ml-analysis.html"].includes(currentPath);
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
  if (protectedPage) protectedPage.hidden = false;
  const homeLoginCta = document.getElementById("home-login-cta");
  if (homeLoginCta) homeLoginCta.hidden = isAuthenticated;
  applyApprovedNavigation(isAuthenticated);

  if (isAuthenticated) {
    void getCurrentUser(localStorage.getItem("token")).then((user) => {
      localStorage.setItem("username", user.username);
      localStorage.setItem("role", user.role);
      applyApprovedNavigation(true);
    }).catch(() => {
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      localStorage.removeItem("role");
      window.location.replace("/login.html");
    });
  }

  if (isAuthenticated) void initDashboard();
  if (isAuthenticated && isCreateReportPage) void initReportWizard();
  if (isAuthenticated && currentPath.endsWith("/report-detail.html")) void initReportDetail();
  if (isAuthenticated && currentPath.endsWith("/profile.html")) void initProfile();
  if (isAuthenticated && currentPath.endsWith("/experts.html")) void initAdminUsers();
  if (isAuthenticated && currentPath.endsWith("/references.html")) void initReferenceCatalog();
  if (isAuthenticated && currentPath.endsWith("/market-data.html")) void initMarketData();
  if (isAuthenticated && currentPath.endsWith("/ml-analysis.html")) void initAnalytics();
  if (currentPath.endsWith("/passport.html")) void initPublicPassport();

  const burgerBtn = document.getElementById("burger-btn");
  const mainNav = document.getElementById("main-nav");
  if (burgerBtn && mainNav) {
    burgerBtn.addEventListener("click", () => {
      burgerBtn.classList.toggle("is-active");
      mainNav.classList.toggle("is-active");
      burgerBtn.setAttribute("aria-expanded", String(mainNav.classList.contains("is-active")));
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
          errorMessage.textContent = `Помилка: ${error.message}`;
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
