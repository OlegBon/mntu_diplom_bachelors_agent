import { checkAuth, logout } from "./modules/auth.js";
import { loginUser } from "./modules/api.js";
import { initDashboard } from "./modules/dashboard.js";
import { initReportWizard } from "./modules/report-wizard.js";
import { initReportDetail } from "./modules/report-detail.js";
import { initPublicPassport } from "./modules/public-passport.js";

function createNavigationLink(href, label, className = "") {
  const item = document.createElement("li");
  if (className) item.className = className;
  const link = document.createElement("a");
  link.href = href;
  link.textContent = label;
  item.append(link);
  return item;
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
  const isAdmin = username === "admin";
  const createReportAction = document.getElementById("create-report-action");
  if (createReportAction) createReportAction.hidden = isAdmin;

  sessionName.replaceChildren();
  const sessionUsername = document.createElement("span");
  sessionUsername.className = "header-session-username";
  sessionUsername.textContent = isAdmin ? "Admin" : username;
  const sessionRole = document.createElement("span");
  sessionRole.className = "header-session-role";
  sessionRole.textContent = isAdmin ? "Адміністратор" : "Експерт";
  sessionName.append(sessionUsername, sessionRole);
  sessionName.hidden = false;

  const links = isAdmin
    ? [["/dashboard.html", "Всі звіти"], ["/experts.html", "Експерти"], ["/references.html", "Довідники"], ["/ml-analysis.html", "Аналітика"], ["/profile.html", "Профіль"]]
    : [["/dashboard.html", "Всі звіти"], ["/create-report.html", "Новий звіт"], ["/profile.html", "Профіль"]];
  for (const [href, label] of links) navList.append(createNavigationLink(href, label));

  const mobileAccount = document.createElement("li");
  mobileAccount.className = "mobile-account";
  const accountName = document.createElement("span");
  accountName.className = "mobile-account-name";
  accountName.textContent = isAdmin ? "Admin" : username;
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
  const isAuthenticated = checkAuth();
  const isAdmin = localStorage.getItem("username") === "admin";
  const currentPath = window.location.pathname;
  const isProtectedPage = ["/dashboard.html", "/create-report.html", "/report-detail.html"].includes(currentPath);
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
  applyApprovedNavigation(isAuthenticated);

  if (isAuthenticated) void initDashboard();
  if (isAuthenticated && isCreateReportPage) void initReportWizard();
  if (isAuthenticated && currentPath.endsWith("/report-detail.html")) void initReportDetail();
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
      const query = document.getElementById("search-input").value.trim();
      if (query) window.location.href = `/passport.html?id=${encodeURIComponent(query)}`;
    });
  }
});
