// Перевірка авторизації користувача
export const checkAuth = () => {
  const token = localStorage.getItem("token");
  return !!token;
};

// Вихід із системи
export const logout = (destination = "/") => {
  localStorage.clear();
  window.location.href = typeof destination === "string" ? destination : "/";
};
