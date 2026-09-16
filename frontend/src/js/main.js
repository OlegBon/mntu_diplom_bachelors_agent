import { checkAuth, logout } from "./modules/auth.js";
import { loginUser, uploadReportMedia } from "./modules/api.js";
import { initDashboard } from "./modules/dashboard.js";
import { initReportWizard } from "./modules/report-wizard.js";
import { initReportDetail } from "./modules/report-detail.js";

// === КОНФІГУРАЦІЯ API ===
const API_URL = "http://127.0.0.1:8000"; // Адреса твого Python сервера

// === ЗМІННІ ДЛЯ DASHBOARD ===
function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character]);
}

function renderPublicNavigation() {
  const navList = document.getElementById("nav-list");
  if (!navList) return;

  navList.replaceChildren();
  for (const [href, label] of [["/", "Головна"], ["/#public-passport", "Перевірити паспорт"]]) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = href;
    link.textContent = label;
    item.append(link);
    navList.append(item);
  }
}

let currentPage = 1;
const itemsPerPage = 50;

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
    const mobileLogin = createNavigationLink("/login.html", "Увійти", "mobile-login");
    navList.append(mobileLogin);
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
    ? [
        ["/dashboard.html", "Всі звіти"],
        ["/experts.html", "Експерти"],
        ["/references.html", "Довідники"],
        ["/ml-analysis.html", "Аналітика"],
        ["/profile.html", "Профіль"],
      ]
    : [
        ["/dashboard.html", "Всі звіти"],
        ["/create-report.html", "Новий звіт"],
        ["/profile.html", "Профіль"],
      ];

  for (const [href, label] of links) {
    navList.append(createNavigationLink(href, label));
  }

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

// === MAPPINGS (Для перекладу кодів з бази в текст) ===
const MAPPINGS = {
  colors: [
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S-Z",
    "Fancy",
  ],
  clarities: [
    "FL",
    "IF",
    "VVS1",
    "VVS2",
    "VS1",
    "VS2",
    "SI1",
    "SI2",
    "I1",
    "I2",
    "I3",
  ],
  cuts: ["Excellent", "Very Good", "Good", "Fair", "Poor"],
};

// --- Helper для API запитів ---
async function apiRequest(endpoint, method = "GET", data = null) {
  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json" };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = { method, headers };
  if (data) config.body = JSON.stringify(data);

  try {
    const response = await fetch(`${API_URL}${endpoint}`, config);

    if (response.status === 401) {
      console.warn("Unauthorized or Token Expired");
      logout("/login.html");
      return null;
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "API Error");
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    alert(`Помилка сервера: ${error.message}`);
    return null;
  }
}

// --- Redirect from /index.html to / ---
if (window.location.pathname.endsWith("/index.html")) {
  window.history.replaceState({}, "", "/");
}

// --- Оновлення Хедера (UI) ---
function updateHeaderUI(isAuthenticated) {
  const authBlock = document.getElementById("auth-block");
  const navList = document.getElementById("nav-list");

  if (!authBlock) return;

  if (isAuthenticated) {
    const username = localStorage.getItem("username") || "User";
    let displayName = username;
    let roleClass = "text-expert";

    if (username === "admin") {
      displayName = "Admin";
      roleClass = "text-admin";
    } else if (username === "expert_1") {
      displayName = "Bondarenko O.";
    }

    const safeDisplayName = escapeHtml(displayName);

    authBlock.innerHTML = `
            <div class="user-trigger" id="user-trigger">
                <span class="user-name ${roleClass}">${safeDisplayName}</span>
                <span class="arrow-icon">▼</span>
            </div>
            <div class="user-dropdown-menu" id="user-dropdown">
                <a href="/profile.html">👤 Мій профіль</a>
                <div class="divider"></div>
                <button id="logout-btn" class="logout-btn">🚪 Вихід</button>
            </div>
        `;

    const trigger = document.getElementById("user-trigger");
    const dropdown = document.getElementById("user-dropdown");
    const logoutBtn = document.getElementById("logout-btn");

    if (trigger) {
      trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        dropdown.classList.toggle("is-visible");
        trigger.classList.toggle("is-active");
      });
    }

    if (logoutBtn) logoutBtn.addEventListener("click", logout);

    document.addEventListener("click", (e) => {
      if (!authBlock.contains(e.target) && dropdown) {
        dropdown.classList.remove("is-visible");
        trigger.classList.remove("is-active");
      }
    });

    if (navList && !document.getElementById("nav-dashboard")) {
      navList.innerHTML = `
                <li id="nav-dashboard"><a href="/dashboard.html">Звіти</a></li>
                <li id="nav-create"><a href="/create-report.html">Новий звіт</a></li>
                <li id="nav-analytics"><a href="/ml-analysis.html">Аналітика</a></li>
             `;
    }
  } else {
    authBlock.innerHTML = `<a class="btn btn-sm btn-primary" href="/login.html">Вхід</a>`;
    if (navList) navList.innerHTML = `<li><a href="/">Головна</a></li>`;
  }
}

// === Функція завантаження Dashboard ===
async function loadDashboard(page = 1) {
  const dashboardTable = document.querySelector(".data-table tbody");
  if (!dashboardTable) return;

  // 1. Збираємо фільтри
  // Шукаємо селекти всередині блоку .filters-bar
  const statusFilter =
    document.querySelector(".filters-bar select option:checked")?.parentElement
      ?.value === "active"
      ? "active"
      : document.querySelector(".filters-bar select option:checked")
            ?.parentElement?.value === "sold"
        ? "sold"
        : document.querySelector('select[name="status"]')?.value || "all";

  // Щоб точно знайти правильні селекти, краще орієнтуватися по порядку або name, якщо він є
  // Але спробуємо знайти їх через .filters-group select
  const filters = document.querySelectorAll(".filters-group .form-select");
  let statusVal = "all";
  let sortVal = "newest";

  if (filters.length >= 2) {
    statusVal = filters[0].value; // Перший селект - статус
    sortVal = filters[1].value; // Другий - сортування
  }

  // Пошук
  const searchInput = document.querySelector(".search-bar input");
  const searchQuery = searchInput ? searchInput.value.trim() : "";

  // 2. Параметри URL
  const skip = (page - 1) * itemsPerPage;
  const params = new URLSearchParams({
    skip: skip,
    limit: itemsPerPage,
  });

  if (statusVal !== "all") params.append("status", statusVal);
  if (sortVal !== "newest") params.append("sort_by", sortVal);
  if (searchQuery) params.append("search", searchQuery);

  // 3. UI
  dashboardTable.innerHTML =
    '<tr><td colspan="10" class="text-center py-4">⏳ Завантаження даних...</td></tr>';

  try {
    // Запит до API на сервер
    const reports = await apiRequest(`/diamonds/?${params.toString()}`);

    dashboardTable.innerHTML = "";

    if (!reports || reports.length === 0) {
      dashboardTable.innerHTML =
        '<tr><td colspan="10" class="text-center py-4">📭 Нічого не знайдено</td></tr>';
      return;
    }

    renderTableRows(reports, dashboardTable);
    currentPage = page;
  } catch (error) {
    console.error("Dashboard Load Error:", error);
    dashboardTable.innerHTML =
      '<tr><td colspan="10" class="text-center text-danger">❌ Помилка завантаження</td></tr>';
  }
}

// === Рендеринг рядків таблиці ===
function renderTableRows(reports, tableElement) {
  reports.forEach((item) => {
    // --- Дата та Час ---
    const dateObj = new Date(item.report_date);
    const dateStr = dateObj.toLocaleDateString("uk-UA", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
    const timeStr = dateObj.toLocaleTimeString("uk-UA", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const dateCellHtml = `
            <div style="line-height: 1.2;">
                <div class="fw-bold" style="font-size: 0.9rem; color: #334155;">${dateStr}</div>
                <div class="text-muted" style="font-size: 0.75rem;">${timeStr}</div>
            </div>
        `;

    // --- Мапінги ---
    const shapeName = item.shape || "Round";
    const colorName = MAPPINGS.colors[item.color_grade] || item.color_grade;
    const clarityName =
      MAPPINGS.clarities[item.clarity_grade] || item.clarity_grade;
    const cutName = MAPPINGS.cuts[item.cut_grade] || "N/A";

    // Badges
    let cutBadge = `<span class="text-muted">${cutName.substring(0, 2)}</span>`;
    if (item.cut_grade === 0)
      cutBadge = `<span class="status-badge active">Ex</span>`;
    else if (item.cut_grade === 1)
      cutBadge = `<span class="status-badge very-good">VG</span>`;

    const statusBadge = item.is_sold
      ? `<span class="status-badge sold">Sold</span>`
      : `<span class="status-badge active">Active</span>`;

    const price = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(item.price);

    // --- HTML Рядка ---
    const row = `
            <tr>
                <td><a class="id-link" href="/view-report.html?id=${item.report_id}">${item.report_id}</a></td>
                
                <td>${dateCellHtml}</td>
                
                <td>${shapeName}</td> 
                <td class="fw-bold">${item.carat_weight}</td>
                <td>${colorName}</td>
                <td>${clarityName}</td>
                <td>${cutBadge}</td>
                <td>${price}</td>
                <td>${statusBadge}</td>
                
                <td>
                    <div class="actions">
                        <button class="table-action" type="button">Редагувати</button>
                        <button class="table-action" type="button">Друк</button>
                        <a href="/view-report.html?id=${item.report_id}" class="table-action">Переглянути</a>
                    </div>
                </td>
            </tr>
        `;
    tableElement.insertAdjacentHTML("beforeend", row);
  });
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

  // === DASHBOARD INITIALIZATION ===
  if (isAuthenticated) void initDashboard();
  if (isAuthenticated && isCreateReportPage) void initReportWizard();
  if (isAuthenticated && currentPath.endsWith("/report-detail.html")) void initReportDetail();

  // --- Mobile Menu ---
  const burgerBtn = document.getElementById("burger-btn");
  const mainNav = document.getElementById("main-nav");
  if (burgerBtn && mainNav) {
    burgerBtn.addEventListener("click", () => {
      burgerBtn.classList.toggle("is-active");
      mainNav.classList.toggle("is-active");
      burgerBtn.setAttribute(
        "aria-expanded",
        String(mainNav.classList.contains("is-active")),
      );
    });
  }

  // --- Login Page Logic ---
  if (window.location.pathname.includes("login.html")) {
    if (isAuthenticated) window.location.href = "/";

    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = loginForm.username.value;
        const password = loginForm.password.value;
        const errorMsg = document.getElementById("error-msg");

        try {
          const token = await loginUser(username, password);
          localStorage.setItem("token", token);
          localStorage.setItem("username", username);
          window.location.href = "/";
        } catch (err) {
          errorMsg.textContent = "Помилка: " + err.message;
          errorMsg.style.display = "block";
        }
      });
    }
  }

  // --- Public Search (Landing) ---
  const searchForm = document.getElementById("public-search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = document.getElementById("search-input").value.trim();
      if (query)
        window.location.href = `/view-report.html?id=${encodeURIComponent(query)}`;
    });
  }

  // --- Create Report Wizard Logic (KEEP EXISTING) ---
  const wizardForm = document.getElementById("legacy-wizard-form");
  if (wizardForm) {
    const dateInput = document.getElementById("input-date");
    if (dateInput) dateInput.valueAsDate = new Date();

    const tabs = document.querySelectorAll(".stepper-tabs .tab");
    const steps = document.querySelectorAll(".step-content");
    const nextBtn = document.getElementById("next-btn");
    const prevBtn = document.getElementById("prev-btn");
    const saveBtn = document.getElementById("save-btn");
    const mediaInputs = [
      { input: document.getElementById("plotting-image"), preview: document.getElementById("plotting-preview"), assetType: "plotting_diagram" },
      { input: document.getElementById("real-image"), preview: document.getElementById("stone-preview"), assetType: "stone_photo" },
    ];

    mediaInputs.forEach(({ input, preview }) => {
      if (!input || !preview) return;
      input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (!file) return;
        const objectUrl = URL.createObjectURL(file);
        preview.src = objectUrl;
        preview.alt = `Попередній перегляд: ${file.name}`;
        preview.addEventListener("load", () => URL.revokeObjectURL(objectUrl), { once: true });
      });
    });

    let currentStep = 1;
    const totalSteps = steps.length;

    function updateUI() {
      steps.forEach((step) => {
        step.classList.remove("active");
        if (parseInt(step.dataset.step) === currentStep)
          step.classList.add("active");
      });
      tabs.forEach((tab) => {
        const stepNum = parseInt(tab.dataset.step);
        tab.classList.toggle("active", stepNum === currentStep);
      });
      if (prevBtn) prevBtn.disabled = currentStep === 1;
      if (currentStep === totalSteps) {
        if (nextBtn) nextBtn.style.display = "none";
        if (saveBtn) saveBtn.style.display = "inline-block";
      } else {
        if (nextBtn) nextBtn.style.display = "inline-block";
        if (saveBtn) saveBtn.style.display = "none";
      }
    }

    if (nextBtn)
      nextBtn.addEventListener("click", () => {
        if (currentStep < totalSteps) {
          currentStep++;
          updateUI();
          window.scrollTo({ top: 100, behavior: "smooth" });
        }
      });

    if (prevBtn)
      prevBtn.addEventListener("click", () => {
        if (currentStep > 1) {
          currentStep--;
          updateUI();
        }
      });

    // --- API: Create Report ---
    wizardForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const btn = document.getElementById("save-btn");
      const originalText = btn.innerText;
      btn.disabled = true;
      btn.innerText = "⏳ Збереження...";

      const formData = new FormData(wizardForm);

      const payload = {
        shape: "Round", // Хардкод поки що, бо немає селекта в візарді
        stone_origin: parseInt(formData.get("stone_origin") || 0),
        carat_weight: parseFloat(formData.get("carat_weight") || 0),
        color_grade: parseInt(formData.get("color_grade") || 0),
        clarity_grade: parseInt(formData.get("clarity_grade") || 0),
        measurements_length: parseFloat(
          formData.get("measurements_length") || 0,
        ),
        measurements_width: parseFloat(formData.get("measurements_width") || 0),
        measurements_depth: parseFloat(formData.get("measurements_depth") || 0),
        table_percent: parseFloat(formData.get("table_percent") || 0),
        depth_percent: parseFloat(formData.get("depth_percent") || 0),
        crown_angle: parseFloat(formData.get("crown_angle") || 0),
        pavilion_angle: parseFloat(formData.get("pavilion_angle") || 0),
        girdle_thickness: formData.get("girdle_thickness"),
        culet_size: formData.get("culet_size"),
        polish_grade: parseInt(formData.get("polish_grade") || 0),
        symmetry_grade: parseInt(formData.get("symmetry_grade") || 0),
        fluorescence_grade: parseInt(formData.get("fluorescence_grade") || 0),
        expert_comment: formData.get("expert_comment"),
        cut_grade: parseInt(
          document.getElementById("calc-cut-grade")?.value || 3,
        ),
        proportions_grade: parseInt(
          document.getElementById("calc-proportions-grade")?.value || 3,
        ),
        price:
          parseFloat(
            (document.getElementById("calc-price")?.value || "0").replace(
              /[^0-9.]/g,
              "",
            ),
          ) || 0,
      };

      const result = await apiRequest("/diamonds/", "POST", payload);

      if (result) {
        const selectedMedia = mediaInputs.filter(({ input }) => input?.files?.[0]);
        let mediaUploadFailed = false;
        for (const { input, assetType } of selectedMedia) {
          try {
            await uploadReportMedia(
              result.report_id,
              assetType,
              input.files[0],
              localStorage.getItem("token"),
            );
          } catch (error) {
            console.error("Report media upload failed", error);
            mediaUploadFailed = true;
          }
        }
        alert(
          mediaUploadFailed
            ? `Звіт ${result.report_id} створено, але одне або кілька вкладень не завантажилися.`
            : `✅ Звіт ${result.report_id} успішно створено!`,
        );
        window.location.href = "/dashboard.html";
      } else {
        btn.disabled = false;
        btn.innerText = originalText;
      }
    });
  }

  // --- Live Calculator Logic (Full) ---
  const calcInputs = document.querySelectorAll(
    "#legacy-wizard-form input, #legacy-wizard-form select",
  );
  const resProp = document.getElementById("res-prop");
  const resPol = document.getElementById("res-pol");
  const resSym = document.getElementById("res-sym");
  const resFinal = document.getElementById("res-final");
  const resPrice = document.getElementById("res-price");
  const hiddenCut = document.getElementById("calc-cut-grade");
  const hiddenProp = document.getElementById("calc-proportions-grade");
  const hiddenPrice = document.getElementById("calc-price");

  if (calcInputs.length > 0) {
    calcInputs.forEach((input) => {
      input.addEventListener("input", updateCalculator);
      input.addEventListener("change", updateCalculator);
    });
    updateCalculator();
  }

  function updateCalculator() {
    const table =
      parseFloat(
        document.querySelector('input[name="table_percent"]')?.value,
      ) || 0;
    const depth =
      parseFloat(
        document.querySelector('input[name="depth_percent"]')?.value,
      ) || 0;
    const crown =
      parseFloat(document.querySelector('input[name="crown_angle"]')?.value) ||
      0;
    const pav =
      parseFloat(
        document.querySelector('input[name="pavilion_angle"]')?.value,
      ) || 0;
    const carat =
      parseFloat(document.querySelector('input[name="carat_weight"]')?.value) ||
      0;
    const polInput = document.querySelector('select[name="polish_grade"]');
    const symInput = document.querySelector('select[name="symmetry_grade"]');
    const polVal = polInput ? parseInt(polInput.value) : 0;
    const symVal = symInput ? parseInt(symInput.value) : 0;

    let propScore = 3;
    if (table > 0 && depth > 0 && crown > 0 && pav > 0) {
      const isEx =
        table >= 56 &&
        table <= 61 &&
        depth >= 59 &&
        depth <= 62.5 &&
        crown >= 34.0 &&
        crown <= 35.0 &&
        pav >= 40.6 &&
        pav <= 41.0;
      const isVG =
        table >= 53 &&
        table <= 63 &&
        depth >= 58 &&
        depth <= 63.5 &&
        crown >= 32.5 &&
        crown <= 36.0 &&
        pav >= 40.2 &&
        pav <= 41.8;
      const isGood = table >= 51 && table <= 66 && depth >= 56 && depth <= 65;
      if (isEx) propScore = 0;
      else if (isVG) propScore = 1;
      else if (isGood) propScore = 2;
      else propScore = 3;
    } else {
      propScore = -1;
    }

    const grades = ["Excellent", "Very Good", "Good", "Fair"];
    const getLabel = (score) =>
      score >= 0 && score < grades.length ? grades[score] : "--";

    if (resProp) {
      resProp.textContent = getLabel(propScore);
      resProp.classList.toggle("placeholder", propScore === -1);
    }
    if (resPol) resPol.textContent = getLabel(polVal);
    if (resSym) resSym.textContent = getLabel(symVal);

    let finalScore = 3;
    if (propScore !== -1) finalScore = Math.max(propScore, polVal, symVal);
    else finalScore = -1;

    if (resFinal) {
      resFinal.textContent = getLabel(finalScore);
      resFinal.className = "calc-value";
      if (finalScore === 0) resFinal.classList.add("price");
      if (finalScore === -1) resFinal.classList.add("placeholder");
      if (hiddenCut) hiddenCut.value = finalScore === -1 ? 3 : finalScore;
      if (hiddenProp) hiddenProp.value = propScore === -1 ? 3 : propScore;
    }

    if (carat > 0) {
      let basePrice = 6000;
      let multiplier = 1.0;
      if (finalScore !== -1) {
        if (finalScore === 0) multiplier = 1.15;
        else if (finalScore === 1) multiplier = 1.05;
        else if (finalScore === 2) multiplier = 0.9;
        else multiplier = 0.8;
      } else {
        multiplier = 0.95;
      }

      const finalPrice = Math.round(carat * basePrice * multiplier);
      const priceFormatted = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(finalPrice);

      if (resPrice) {
        resPrice.textContent = priceFormatted;
        resPrice.classList.remove("placeholder");
      }
      if (hiddenPrice) hiddenPrice.value = finalPrice;
    } else {
      if (resPrice) {
        resPrice.textContent = "$ --,--";
        resPrice.classList.add("placeholder");
      }
    }
  }
});
