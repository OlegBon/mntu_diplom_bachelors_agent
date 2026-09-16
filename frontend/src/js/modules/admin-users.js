import { createUser, getCurrentUser, getUsers, setUserActivation, updateUser } from "./api.js";

function setStatus(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("is-error", isError);
  element.hidden = false;
}

function makeCell(value) {
  const cell = document.createElement("td");
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
  let currentUser;
  async function load() {
    currentUser = await getCurrentUser(token);
    if (currentUser.role !== "admin") throw new Error("Ця сторінка доступна лише адміністратору.");
    const users = await getUsers(token);
    body.replaceChildren();
    for (const user of users) {
      const row = document.createElement("tr");
      row.append(makeCell(user.username), makeCell([user.last_name, user.first_name, user.middle_name].filter(Boolean).join(" ")));
      const roleCell = document.createElement("td");
      const role = document.createElement("select");
      role.className = "form-select";
      for (const [value, label] of [["gemologist", "Експерт"], ["admin", "Адміністратор"]]) {
        const option = document.createElement("option"); option.value = value; option.textContent = label; option.selected = user.role === value; role.append(option);
      }
      role.addEventListener("change", async () => {
        try { await updateUser(user.expert_id, { role: role.value }, token); setStatus(status, "Роль оновлено."); await load(); }
        catch (error) { setStatus(status, error.message, true); role.value = user.role; }
      });
      roleCell.append(role);
      row.append(roleCell, makeCell(user.is_active ? "Активний" : "Неактивний"));
      const actions = document.createElement("td");
      const activation = document.createElement("button");
      activation.type = "button"; activation.className = "btn btn-outline btn-sm";
      activation.textContent = user.is_active ? "Деактивувати" : "Активувати";
      activation.disabled = user.expert_id === currentUser.expert_id;
      activation.addEventListener("click", async () => {
        activation.disabled = true;
        try { await setUserActivation(user.expert_id, !user.is_active, token); setStatus(status, "Стан облікового запису оновлено."); await load(); }
        catch (error) { setStatus(status, error.message, true); activation.disabled = false; }
      });
      actions.append(activation); row.append(actions); body.append(row);
    }
  }
  try { await load(); } catch (error) { setStatus(status, error.message, true); return; }
  createForm.addEventListener("submit", async (event) => {
    event.preventDefault(); const button = createForm.querySelector("button[type='submit']"); button.disabled = true;
    try { await createUser(Object.fromEntries(new FormData(createForm)), token); createForm.reset(); setStatus(status, "Експерта створено."); await load(); }
    catch (error) { setStatus(status, error.message, true); } finally { button.disabled = false; }
  });
}
