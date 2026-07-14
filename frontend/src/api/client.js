import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const client = axios.create({ baseURL: API_URL });

function getTokens() {
  const raw = localStorage.getItem("sistema_ra_tokens");
  return raw ? JSON.parse(raw) : null;
}

function setTokens(tokens) {
  if (tokens) {
    localStorage.setItem("sistema_ra_tokens", JSON.stringify(tokens));
  } else {
    localStorage.removeItem("sistema_ra_tokens");
  }
}

client.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

let refrescando = null;

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const tokens = getTokens();
      if (!tokens?.refresh) {
        setTokens(null);
        return Promise.reject(error);
      }
      try {
        refrescando =
          refrescando ||
          axios.post(`${API_URL}/auth/login/refresh/`, { refresh: tokens.refresh });
        const { data } = await refrescando;
        refrescando = null;
        setTokens({ ...tokens, access: data.access });
        original.headers.Authorization = `Bearer ${data.access}`;
        return client(original);
      } catch (refreshError) {
        refrescando = null;
        setTokens(null);
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export async function login(username, password) {
  const { data } = await axios.post(`${API_URL}/auth/login/`, { username, password });
  setTokens(data);
  return data;
}

export function logout() {
  setTokens(null);
}

export function estaAutenticado() {
  return !!getTokens()?.access;
}

export default client;
