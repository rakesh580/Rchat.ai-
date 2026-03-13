// In production (HF Spaces), backend is same origin; in dev, use localhost:8000
const API_HOST = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");
const BASE_URL = `${API_HOST}/api/v1`;

export { API_HOST };

export async function api(endpoint, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers,
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    throw new Error("Invalid response from server");
  }

  if (!res.ok) {
    const message = data.detail || "Something went wrong";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export async function apiUpload(endpoint, { file, token } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers,
    credentials: "include",
    body: formData,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    throw new Error("Invalid response from server");
  }

  if (!res.ok) {
    const message = data.detail || "Upload failed";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}
