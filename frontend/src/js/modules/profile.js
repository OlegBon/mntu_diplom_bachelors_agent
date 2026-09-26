import { getCurrentUser, updateMyDemoAccess, updateMyPassword, updateMyProfile } from "./api.js";

function setStatus(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("is-error", isError);
  element.hidden = false;
}

export async function initProfile() {
  const page = document.querySelector("[data-profile-page]");
  if (!page) return;
  const token = localStorage.getItem("token");
  const profileForm = document.getElementById("profile-form");
  const passwordForm = document.getElementById("password-form");
  const demoAccessForm = document.getElementById("demo-access-form");
  const status = document.getElementById("profile-status");
  let currentUser;
  try {
    currentUser = await getCurrentUser(token);
    const usernameInput = document.getElementById("profile-username");
    usernameInput.value = currentUser.username;
    usernameInput.disabled = currentUser.role !== "admin";
    document.getElementById("profile-role").value = currentUser.role === "admin" ? "Адміністратор" : "Експерт";
    for (const field of ["first_name", "last_name", "middle_name"]) {
      profileForm.elements[field].value = currentUser[field] || "";
    }
    if (currentUser.role === "admin") {
      document.getElementById("demo-access-surface").hidden = false;
      demoAccessForm.elements.demo_access_enabled.checked = currentUser.demo_access_enabled;
    }
  } catch (error) {
    setStatus(status, error.message, true);
    return;
  }
  profileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = profileForm.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      const saved = await updateMyProfile(Object.fromEntries(new FormData(profileForm)), token);
      if (saved.username !== currentUser.username) {
        localStorage.clear(); window.location.replace("/login.html"); return;
      }
      localStorage.setItem("username", saved.username);
      setStatus(status, "Дані профілю збережено.");
    } catch (error) {
      setStatus(status, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  if (demoAccessForm) demoAccessForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = demoAccessForm.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      const saved = await updateMyDemoAccess(demoAccessForm.elements.demo_access_enabled.checked, token);
      currentUser = saved;
      localStorage.setItem("demo_access_enabled", String(saved.demo_access_enabled));
      window.dispatchEvent(new CustomEvent("demo-access-changed", { detail: saved }));
      setStatus(status, saved.demo_access_enabled ? "Доступ до «Демо» увімкнено." : "Доступ до «Демо» вимкнено.");
    } catch (error) {
      setStatus(status, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  passwordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newPassword = passwordForm.elements.new_password.value;
    if (newPassword !== passwordForm.elements.confirm_password.value) {
      setStatus(status, "Новий пароль і підтвердження не збігаються.", true);
      return;
    }
    const button = passwordForm.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      await updateMyPassword({ current_password: passwordForm.elements.current_password.value, new_password: newPassword }, token);
      passwordForm.reset();
      setStatus(status, "Пароль змінено.");
    } catch (error) {
      setStatus(status, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}
