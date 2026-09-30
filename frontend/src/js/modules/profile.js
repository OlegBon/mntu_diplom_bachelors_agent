import { getCurrentUser, updateMyDemoAccess, updateMyPartnerControlsAccess, updateMyPassword, updateMyProfile } from "./api.js";
import { t } from "./i18n.js";

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
  const partnerControlsForm = document.getElementById("partner-controls-form");
  const status = document.getElementById("profile-status");
  let currentUser;
  try {
    currentUser = await getCurrentUser(token);
    const usernameInput = document.getElementById("profile-username");
    usernameInput.value = currentUser.username;
    usernameInput.disabled = currentUser.role !== "admin";
    document.getElementById("profile-role").value = currentUser.role === "admin" ? t("auth.administrator") : t("auth.gemologist");
    for (const field of ["first_name", "last_name", "middle_name"]) {
      profileForm.elements[field].value = currentUser[field] || "";
    }
    if (currentUser.role === "admin") {
      document.getElementById("demo-access-surface").hidden = false;
      document.getElementById("partner-controls-surface").hidden = false;
      demoAccessForm.elements.demo_access_enabled.checked = currentUser.demo_access_enabled;
      partnerControlsForm.elements.partner_controls_enabled.checked = currentUser.partner_controls_enabled;
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
      setStatus(status, t("profile.saved"));
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
      setStatus(status, t(saved.demo_access_enabled ? "profile.demoEnabled" : "profile.demoDisabled"));
    } catch (error) {
      setStatus(status, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  if (partnerControlsForm) partnerControlsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = partnerControlsForm.querySelector("button[type='submit']"); button.disabled = true;
    try {
      const saved = await updateMyPartnerControlsAccess(partnerControlsForm.elements.partner_controls_enabled.checked, token);
      currentUser = saved;
      setStatus(status, t(saved.partner_controls_enabled ? "profile.partnerEnabled" : "profile.partnerDisabled"));
    } catch (error) { setStatus(status, error.message, true); }
    finally { button.disabled = false; }
  });
  passwordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const newPassword = passwordForm.elements.new_password.value;
    if (newPassword !== passwordForm.elements.confirm_password.value) {
      setStatus(status, t("profile.passwordMismatch"), true);
      return;
    }
    const button = passwordForm.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      await updateMyPassword({ current_password: passwordForm.elements.current_password.value, new_password: newPassword }, token);
      passwordForm.reset();
      setStatus(status, t("profile.passwordChanged"));
    } catch (error) {
      setStatus(status, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}
