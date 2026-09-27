// Перевірка авторизації користувача
export const checkAuth = () => {
  const token = localStorage.getItem("token");
  return !!token;
};

export const isConfirmedUnauthorized = (error) => error?.status === 401;

export const clearSession = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("role");
  localStorage.removeItem("demo_access_enabled");
};

// Вихід із системи
export const logout = (destination = "/") => {
  localStorage.clear();
  window.location.href = typeof destination === "string" ? destination : "/";
};
