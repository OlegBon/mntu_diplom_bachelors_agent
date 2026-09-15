const BASE_URL = "http://127.0.0.1:8000";

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
