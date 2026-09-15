const BASE_URL = "http://127.0.0.1:8000";

export class ApiRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

async function requestApi(path, { method = "GET", token, body } = {}) {
  const headers = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiRequestError(payload?.detail || "Помилка запиту до API", response.status);
  }
  return payload;
}

export const getCurrentUser = (token) => requestApi("/users/me", { token });

export const getExperts = (token) => requestApi("/experts/", { token });

export const getGradeMappings = () => requestApi("/market/mappings");

export const getReportDashboard = (params, token) => {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value !== null && value !== undefined),
  );
  return requestApi(`/reports?${query.toString()}`, { token });
};

/**
 * Функція логіну (отримання токена)
 */
export const loginUser = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  try {
    const response = await fetch(`${BASE_URL}/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Невірний логін або пароль");
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error("Login Error:", error);
    throw error;
  }
};

/** Upload one selected report file after the report itself exists. */
export const uploadReportMedia = async (reportId, assetType, file, token) => {
  const formData = new FormData();
  formData.append("asset_type", assetType);
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/reports/${encodeURIComponent(reportId)}/media`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Не вдалося завантажити вкладення звіту");
  }
  return response.json();
};
