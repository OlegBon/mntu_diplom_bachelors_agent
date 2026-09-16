import { createUser, getCurrentUser, getUsers, setUserActivation, updateUser } from "./api.js";
import { renderPagination } from "./pagination.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";

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
    activationButton.textContent = user.is_active ? "Деактивувати" : "Активувати";
    activationButton.disabled = user.expert_id === currentUser.expert_id;
    dialog.showModal();
  }
  async function load() {
    currentUser = await getCurrentUser(token);
    if (currentUser.role !== "admin") throw new Error("Ця сторінка доступна лише адміністратору.");
    const response = await getUsers({ ...state, page_size: 10 }, token);
    const users = response.items;
    body.replaceChildren();
    for (const user of users) {
      const row = document.createElement("tr");
      row.append(makeCell(user.username, "Username"), makeCell([user.last_name, user.first_name, user.middle_name].filter(Boolean).join(" "), "Ім’я"), makeCell(user.role === "admin" ? "Адміністратор" : "Експерт", "Роль"), makeCell(user.is_active ? "Активний" : "Неактивний", "Стан"));
      const actions = document.createElement("td");
      actions.dataset.label = "Дії";
      const edit = document.createElement("button"); edit.type = "button"; edit.className = "btn btn-outline btn-sm"; edit.textContent = "Змінити";
      edit.addEventListener("click", () => openDialog(user)); actions.append(edit); row.append(actions); body.append(row);
    }
    renderPagination(pagination, { page: response.page, totalPages: response.total_pages, onPageChange: async (page) => { state.page = page; await load(); } });
  }
  try { await load(); } catch (error) { setStatus(status, error.message, true); return; }
  createForm.addEventListener("submit", async (event) => {
    event.preventDefault(); const button = createForm.querySelector("button[type='submit']"); button.disabled = true;
    try { await createUser(Object.fromEntries(new FormData(createForm)), token); createForm.reset(); setStatus(status, "Експерта створено."); state.page = 1; await load(); }
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
      dialog.close(); setStatus(status, "Обліковий запис оновлено."); await load();
    } catch (error) { setStatus(status, error.message, true); } finally { save.disabled = false; }
  });
  activationButton.addEventListener("click", async () => {
    activationButton.disabled = true;
    try { await setUserActivation(selectedUser.expert_id, !selectedUser.is_active, token); dialog.close(); setStatus(status, "Стан облікового запису оновлено."); await load(); }
    catch (error) { setStatus(status, error.message, true); activationButton.disabled = false; }
  });
}
