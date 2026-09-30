import { createUser, getCurrentUser, getUsers, setUserActivation, updateUser } from "./api.js";
import { renderPagination } from "./pagination.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";
import { t } from "./i18n.js";

function setStatus(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("is-error", isError);
  element.hidden = false;
}

function makeCell(value, label = "") {
  const cell = document.createElement("td");
  cell.dataset.label = label;
  cell.textContent = value || "—";
  return cell;
}

export async function initAdminUsers() {
  const page = document.querySelector("[data-admin-users-page]");
  if (!page) return;
  const token = localStorage.getItem("token");
  const status = document.getElementById("admin-users-status");
  const body = document.getElementById("admin-users-body");
  const createForm = document.getElementById("admin-user-create-form");
  const searchInput = document.getElementById("admin-users-search");
  const pagination = document.getElementById("admin-users-pagination");
  const dialog = document.getElementById("admin-user-dialog");
  const editForm = document.getElementById("admin-user-edit-form");
  const activationButton = document.getElementById("edit-user-activation");
  let state = { page: 1, search: "" };
  let currentUser;
  let selectedUser;
  function openDialog(user) {
    selectedUser = user;
    editForm.elements.expert_id.value = user.expert_id;
    for (const field of ["username", "first_name", "last_name", "middle_name", "role"]) editForm.elements[field].value = user[field] || "";
    editForm.elements.password.value = "";
    activationButton.textContent = t(user.is_active ? "experts.deactivate" : "experts.activate");
    activationButton.disabled = user.expert_id === currentUser.expert_id;
    dialog.showModal();
  }
  async function load() {
    currentUser = await getCurrentUser(token);
    if (currentUser.role !== "admin") throw new Error(t("experts.adminOnly"));
    const response = await getUsers({ ...state, page_size: 10 }, token);
    const users = response.items;
    body.replaceChildren();
    for (const user of users) {
      const row = document.createElement("tr");
      row.append(makeCell(user.username, t("experts.username")), makeCell([user.last_name, user.first_name, user.middle_name].filter(Boolean).join(" "), t("experts.name")), makeCell(user.role === "admin" ? t("auth.administrator") : t("auth.gemologist"), t("experts.role")), makeCell(user.is_active ? t("experts.active") : t("experts.inactive"), t("experts.state")));
      const actions = document.createElement("td");
      actions.dataset.label = t("experts.actions");
      const edit = document.createElement("button"); edit.type = "button"; edit.className = "btn btn-outline btn-sm"; edit.textContent = t("experts.edit");
      edit.addEventListener("click", () => openDialog(user)); actions.append(edit); row.append(actions); body.append(row);
    }
    renderPagination(pagination, { page: response.page, totalPages: response.total_pages, onPageChange: async (page) => { state.page = page; await load(); } });
  }
  try { await load(); } catch (error) { setStatus(status, error.message, true); return; }
  createForm.addEventListener("submit", async (event) => {
    event.preventDefault(); const button = createForm.querySelector("button[type='submit']"); button.disabled = true;
    try { await createUser(Object.fromEntries(new FormData(createForm)), token); createForm.reset(); setStatus(status, t("experts.created")); state.page = 1; await load(); }
    catch (error) { setStatus(status, error.message, true); } finally { button.disabled = false; }
  });
  searchInput.addEventListener("input", async () => { state = { page: 1, search: searchInput.value.trim() }; await load(); });
  registerVisibleDataRefresh(load, { canRefresh: () => !dialog.open });
  document.getElementById("admin-user-dialog-close").addEventListener("click", () => dialog.close());
  editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const save = document.getElementById("edit-user-save"); save.disabled = true;
    try {
      const payload = Object.fromEntries(new FormData(editForm));
      if (!payload.password) delete payload.password;
      const saved = await updateUser(selectedUser.expert_id, payload, token);
      if (saved.expert_id === currentUser.expert_id && saved.username !== currentUser.username) { localStorage.clear(); window.location.replace("/login.html"); return; }
      dialog.close(); setStatus(status, t("experts.updated")); await load();
    } catch (error) { setStatus(status, error.message, true); } finally { save.disabled = false; }
  });
  activationButton.addEventListener("click", async () => {
    activationButton.disabled = true;
    try { await setUserActivation(selectedUser.expert_id, !selectedUser.is_active, token); dialog.close(); setStatus(status, t("experts.stateUpdated")); await load(); }
    catch (error) { setStatus(status, error.message, true); activationButton.disabled = false; }
  });
}
