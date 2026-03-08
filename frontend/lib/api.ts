/**
 * Axios instance and API helpers for FastAPI backend.
 * JWT is stored in localStorage; 401 triggers redirect to login.
 */
import axios, { AxiosError } from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// Auth
export const auth = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/auth/login", { email, password }),
  register: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/auth/register", { email, password }),
  me: () => api.get("/auth/me"),
};

// Accounts
export interface Account {
  id: string;
  username: string;
  proxy_id: string | null;
  status: string;
  created_at: string;
}

export const accounts = {
  list: () => api.get<Account[]>("/accounts"),
  connect: (data: { username: string; session_cookie?: string; proxy_id?: string; device_profile?: object }) =>
    api.post<Account>("/accounts/connect", data),
  delete: (id: string) => api.delete(`/accounts/${id}`),
};

// Tasks
export interface Task {
  id: string;
  account_id: string;
  task_type: string;
  target: string | null;
  payload: Record<string, unknown> | null;
  status: string;
  scheduled_time: string | null;
  created_at: string;
  completed_at: string | null;
}

export const tasks = {
  list: (params?: { account_id?: string; status_filter?: string }) =>
    api.get<Task[]>("/tasks", { params }),
  create: (data: {
    account_id: string;
    task_type: string;
    target?: string;
    payload?: object;
    scheduled_time?: string;
  }) => api.post<Task>("/tasks/create", data),
  delete: (id: string) => api.delete(`/tasks/${id}`),
};

// Analytics
export interface AnalyticsOverview {
  total_accounts: number;
  tasks_by_status: Record<string, number>;
  tasks_by_type: Record<string, number>;
}

export const analytics = {
  overview: () => api.get<AnalyticsOverview>("/analytics/overview"),
};
