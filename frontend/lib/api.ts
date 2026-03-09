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

export interface SessionCheckResult {
  valid: boolean;
  message: string;
}

export const accounts = {
  list: () => api.get<Account[]>("/accounts"),
  connect: (data: { username: string; session_cookie?: string; proxy_id?: string; device_profile?: object }) =>
    api.post<Account>("/accounts/connect", data),
  checkSession: (id: string) => api.post<SessionCheckResult>(`/accounts/${id}/check-session`),
  delete: (id: string) => api.delete(`/accounts/${id}`),
};

// Tasks
export interface Task {
  id: string;
  account_id: string;
  account_username: string | null; // which account this task is assigned to
  task_type: string;
  target: string | null;
  payload: Record<string, unknown> | null;
  status: string;
  result_message: string | null; // exact reason for success or failure
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
  bulkFollow: (target: string) =>
    api.post<Task[]>("/tasks/bulk-follow", { target: target.replace(/^@/, "") }),
  bulkLike: (target: string) =>
    api.post<Task[]>("/tasks/bulk-like", { target }),
  bulkComment: (target: string, message: string) =>
    api.post<Task[]>("/tasks/bulk-comment", { target, message }),
  bulkViewReel: (target: string, viewsPerAccount?: number) =>
    api.post<Task[]>("/tasks/bulk-view-reel", { target, views_per_account: viewsPerAccount ?? 1 }),
  delete: (id: string) => api.delete(`/tasks/${id}`),
};

// Instagram Graph API (Business/Creator: DMs + Comments)
export const instagramApi = {
  sendDm: (user_id: string, message: string) =>
    api.post("/instagram-api/send-dm", { user_id, message }),
  getComments: (media_id: string) => api.get<{ data: Array<{ id: string; text: string; username?: string }> }>(`/instagram-api/comments/${media_id}`),
  replyToComment: (comment_id: string, message: string) =>
    api.post(`/instagram-api/comments/${comment_id}/reply`, { message }),
  hideComment: (comment_id: string) => api.post(`/instagram-api/comments/${comment_id}/hide`),
  deleteComment: (comment_id: string) => api.delete(`/instagram-api/comments/${comment_id}`),
};

// Settings (testing mode, Instagram reply-all, Comment-to-DM enabled posts)
export const settings = {
  getTestingMode: () => api.get<{ testing_mode: boolean }>("/settings/testing-mode"),
  setTestingMode: (enabled: boolean) =>
    api.post<{ testing_mode: boolean }>("/settings/testing-mode", { testing_mode: enabled }),
  getInstagramReplyAll: () =>
    api.get<{ reply_all: boolean; reply_all_message: string }>("/settings/instagram-reply-all"),
  setInstagramReplyAll: (reply_all: boolean, reply_all_message?: string) =>
    api.post<{ reply_all: boolean; reply_all_message: string }>("/settings/instagram-reply-all", {
      reply_all,
      reply_all_message: reply_all_message ?? undefined,
    }),
  getCommentDmEnabledPosts: () =>
    api.get<{ media_ids: string[] }>("/settings/comment-dm-enabled-posts"),
  addCommentDmEnabledPost: (media_id: string) =>
    api.post<{ media_ids: string[] }>("/settings/comment-dm-enabled-posts", { media_id: media_id.trim() }),
  removeCommentDmEnabledPost: (media_id: string) =>
    api.delete<{ media_ids: string[] }>(`/settings/comment-dm-enabled-posts/${encodeURIComponent(media_id)}`),
  getInstagramFollowerCheck: () =>
    api.get<{ require_follower: boolean; non_follower_message: string }>("/settings/instagram-comment-dm-follower"),
  setInstagramFollowerCheck: (require_follower: boolean, non_follower_message?: string) =>
    api.post<{ require_follower: boolean; non_follower_message: string }>("/settings/instagram-comment-dm-follower", {
      require_follower,
      non_follower_message: non_follower_message ?? undefined,
    }),
  getInstagramDmAllowedUsers: () =>
    api.get<{ user_ids: string[] }>("/settings/instagram-dm-allowed-users"),
  addInstagramDmAllowedUser: (user_id: string) =>
    api.post<{ user_ids: string[] }>("/settings/instagram-dm-allowed-users", { user_id: user_id.trim() }),
  removeInstagramDmAllowedUser: (user_id: string) =>
    api.delete<{ user_ids: string[] }>(`/settings/instagram-dm-allowed-users/${encodeURIComponent(user_id)}`),
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
