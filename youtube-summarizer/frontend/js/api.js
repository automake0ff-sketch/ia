/**
 * api.js — capa de comunicación con el backend FastAPI.
 * Todas las rutas son relativas porque el frontend se sirve desde el
 * mismo origen que la API (ver backend/app/main.py).
 */
const API_BASE = "/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function handleResponse(response) {
  if (response.ok) {
    return response.json();
  }
  let detail = `Error ${response.status}`;
  try {
    const data = await response.json();
    detail = data.detail || detail;
  } catch (_) {
    /* respuesta sin cuerpo JSON */
  }
  throw new ApiError(detail, response.status);
}

const Api = {
  async summarize(payload) {
    const response = await fetch(`${API_BASE}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse(response);
  },

  async getHistory(userId, limit = 100) {
    const params = new URLSearchParams({ user_id: userId, limit: String(limit) });
    const response = await fetch(`${API_BASE}/history?${params.toString()}`);
    return handleResponse(response);
  },

  async deleteHistoryItem(id) {
    const response = await fetch(`${API_BASE}/history/${id}`, { method: "DELETE" });
    return handleResponse(response);
  },

  async clearHistory(userId) {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(`${API_BASE}/history?${params.toString()}`, { method: "DELETE" });
    return handleResponse(response);
  },

  exportUrl(id, format) {
    return `${API_BASE}/export/${id}/${format}`;
  },
};
