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

export const updateMyProfile = (profile, token) => requestApi("/users/me/profile", { method: "PUT", token, body: profile });

export const updateMyPassword = (passwords, token) => requestApi("/users/me/password", { method: "PUT", token, body: passwords });

export const getUsers = (params, token) => {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== "" && value !== undefined));
  return requestApi(`/users/?${query}`, { token });
};

export const createUser = (user, token) => requestApi("/users/", { method: "POST", token, body: user });

export const updateUser = (expertId, user, token) => requestApi(`/users/${expertId}`, { method: "PUT", token, body: user });

export const setUserActivation = (expertId, isActive, token) => requestApi(
  `/users/${expertId}/${isActive ? "activate" : "deactivate"}`,
  { method: "POST", token },
);

export const getExperts = (token) => requestApi("/experts/", { token });

const analyticsQuery = (params = {}) => new URLSearchParams(
  Object.entries(params).filter(([, value]) => value !== "" && value !== null && value !== undefined),
).toString();

function analyticsRequest(path, paramsOrToken, maybeToken) {
  const params = typeof paramsOrToken === "string" ? {} : paramsOrToken;
  const token = typeof paramsOrToken === "string" ? paramsOrToken : maybeToken;
  const query = analyticsQuery(params);
  return requestApi(`${path}${query ? `?${query}` : ""}`, { token });
}

export const getExpertStatistics = (paramsOrToken, maybeToken) => analyticsRequest(
  "/statistics/expert-performance", paramsOrToken, maybeToken,
);

export const getAdminReviewStatistics = (paramsOrToken, maybeToken) => analyticsRequest(
  "/statistics/admin-review-performance", paramsOrToken, maybeToken,
);

export const signalReportWorkSession = (reportId, payload, token) => requestApi(
  `/reports/${encodeURIComponent(reportId)}/work-session`, { method: "POST", token, body: payload },
);

export const startWizardWorkSession = (payload, token) => requestApi(
  "/report-wizard-sessions", { method: "POST", token, body: payload },
);

export const getGradeMappings = () => requestApi("/market/mappings");

export const getReportDashboard = (params, token) => {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value !== null && value !== undefined),
  );
  return requestApi(`/reports?${query.toString()}`, { token });
};

export const getReferenceValues = (token) => requestApi("/reference-values", { token });

export const getMarketDataProviders = (token) => requestApi("/market-data/providers", { token });

export const getMarketReferencePolicy = (token) => requestApi("/market-data/policy", { token });

export const updateMarketReferencePolicy = (policy, token) => requestApi(
  "/market-data/policy", { method: "PUT", token, body: policy },
);

export const getMarketDataSnapshots = (token) => requestApi("/market-data/snapshots", { token });

export const getFxDataSnapshots = (token) => requestApi("/market-data/fx-snapshots", { token });

export const refreshNbuRate = (token) => requestApi("/market-data/providers/nbu/refresh", { method: "POST", token });

export const fetchMarketDataCandidate = (providerCode, token) => requestApi(
  `/market-data/providers/${encodeURIComponent(providerCode)}/fetch`, { method: "POST", token },
);

export const decideMarketDataSnapshot = (snapshotId, action, reason, token) => requestApi(
  `/market-data/snapshots/${encodeURIComponent(snapshotId)}/${action}`,
  { method: "POST", token, body: { reason: reason || null } },
);

export const attachMarketReference = (reportId, payload, token) => requestApi(
  `/reports/${encodeURIComponent(reportId)}/valuations/market-reference`, { method: "POST", token, body: payload },
);

export const getReportValuations = (reportId, token) => requestApi(
  `/reports/${encodeURIComponent(reportId)}/valuations`, { token },
);

export const getNextReportId = (token) => requestApi("/reports/next-id", { token });

export const previewReportCalculation = (stone, token) => requestApi("/reports/preview", { method: "POST", token, body: stone });

export const createDomainReport = (payload, token) => requestApi("/reports", { method: "POST", token, body: payload });

export const getDomainReport = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}`, { token });

export const getPublicPassport = (publicId) => requestApi(`/public/passports/${encodeURIComponent(publicId)}`);

export const getReportPassport = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/passport`, { token });

export const publishReportPassport = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/passport`, { method: "POST", token });

export const reissueReportPassport = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/passport/reissue`, { method: "POST", token });

export const revokeReportPassport = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/passport`, { method: "DELETE", token });

export const getReportPassportQr = async (reportId, publicUrl, token) => {
  const query = new URLSearchParams({ public_url: publicUrl });
  const response = await fetch(`${BASE_URL}/reports/${encodeURIComponent(reportId)}/passport/qr?${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiRequestError(payload?.detail || "Не вдалося створити QR-код", response.status);
  }
  return response.blob();
};

export const getReportPassportPdf = async (reportId, publicUrl, token) => {
  const query = new URLSearchParams({ public_url: publicUrl });
  const response = await fetch(`${BASE_URL}/reports/${encodeURIComponent(reportId)}/passport/pdf?${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiRequestError(payload?.detail || "Не вдалося сформувати PDF-паспорт", response.status);
  }
  return response.blob();
};

export const updateDomainReport = (reportId, payload, token) => requestApi(`/reports/${encodeURIComponent(reportId)}`, { method: "PUT", token, body: payload });

export const transitionDomainReport = (reportId, payload, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/transitions`, { method: "POST", token, body: payload });

export const getReportEvents = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/events`, { token });

export const getReportMedia = (reportId, token) => requestApi(`/reports/${encodeURIComponent(reportId)}/media`, { token });

export const getReportMediaContentUrl = (reportId, mediaId) => `${BASE_URL}/reports/${encodeURIComponent(reportId)}/media/${encodeURIComponent(mediaId)}/content`;

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
