"use client";

import { useEffect, useState } from "react";
import { accounts, tasks, settings, type Account, type Task } from "@/lib/api";
import TaskTable from "@/components/TaskTable";

const TASK_TYPES = [
  { value: "FOLLOW_USER", label: "Follow user" },
  { value: "COMMENT_POST", label: "Comment" },
  { value: "LIKE_POST", label: "Like post" },
  { value: "SEND_DM", label: "Send DM" },
  { value: "UPLOAD_POST", label: "Upload post" },
  { value: "VIEW_REEL", label: "View reel" },
];

export default function AutomationPage() {
  const [taskList, setTaskList] = useState<Task[]>([]);
  const [accountList, setAccountList] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [bulkTarget, setBulkTarget] = useState("");
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkMessage, setBulkMessage] = useState("");
  const [bulkLikeTarget, setBulkLikeTarget] = useState("");
  const [bulkLikeLoading, setBulkLikeLoading] = useState(false);
  const [bulkLikeMessage, setBulkLikeMessage] = useState("");
  const [bulkCommentTarget, setBulkCommentTarget] = useState("");
  const [bulkCommentMessage, setBulkCommentMessage] = useState("");
  const [bulkCommentLoading, setBulkCommentLoading] = useState(false);
  const [bulkCommentResult, setBulkCommentResult] = useState("");
  const [bulkReelTarget, setBulkReelTarget] = useState("");
  const [bulkReelViewsPerAccount, setBulkReelViewsPerAccount] = useState(1);
  const [bulkReelLoading, setBulkReelLoading] = useState(false);
  const [bulkReelMessage, setBulkReelMessage] = useState("");
  const [error, setError] = useState("");
  const [testingMode, setTestingMode] = useState(false);
  const [testingModeLoading, setTestingModeLoading] = useState(false);
  const [form, setForm] = useState({
    account_id: "",
    task_type: "FOLLOW_USER",
    target: "",
    message: "",
    scheduled_time: "",
  });

  const fetchData = () => {
    setLoading(true);
    Promise.all([tasks.list(), accounts.list()])
      .then(([tRes, aRes]) => {
        setTaskList(tRes.data);
        setAccountList(aRes.data);
        if (aRes.data.length > 0 && !form.account_id) setForm((f) => ({ ...f, account_id: aRes.data[0].id }));
      })
      .catch(() => { })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    settings.getTestingMode().then((r) => setTestingMode(r.data.testing_mode)).catch(() => { });
  }, []);

  const handleTestingModeToggle = async (enabled: boolean) => {
    setTestingModeLoading(true);
    try {
      const r = await settings.setTestingMode(enabled);
      setTestingMode(r.data.testing_mode);
    } catch {
      setError("Failed to update testing mode");
    } finally {
      setTestingModeLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      const payload: Record<string, unknown> = {};
      if (form.task_type === "SEND_DM" || form.task_type === "COMMENT_POST") payload.message = form.message;
      const scheduledTimeIso = form.scheduled_time
        ? new Date(form.scheduled_time).toISOString()
        : undefined;
      const { data: created } = await tasks.create({
        account_id: form.account_id,
        task_type: form.task_type,
        target: form.target || undefined,
        payload: Object.keys(payload).length ? payload : undefined,
        scheduled_time: scheduledTimeIso,
      });
      setForm((f) => ({ ...f, target: "", message: "" }));
      setTaskList((prev) => [created, ...prev]);
      fetchData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to create task";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await tasks.delete(id);
      fetchData();
    } catch {
      setError("Failed to delete task");
    }
  };

  const handleBulkFollow = async (e: React.FormEvent) => {
    e.preventDefault();
    const username = bulkTarget.trim().replace(/^@/, "");
    if (!username) {
      setBulkMessage("Enter a username");
      return;
    }
    setError("");
    setBulkMessage("");
    setBulkLoading(true);
    try {
      const { data: created } = await tasks.bulkFollow(username);
      setBulkTarget("");
      setBulkMessage(`Created ${created.length} follow task(s) for @${username}. Tasks are spread over the next 24h.`);
      fetchData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Bulk follow failed";
      setBulkMessage(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setBulkLoading(false);
    }
  };

  const handleBulkLike = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = bulkLikeTarget.trim();
    if (!url) {
      setBulkLikeMessage("Enter a post URL");
      return;
    }
    setError("");
    setBulkLikeMessage("");
    setBulkLikeLoading(true);
    try {
      const { data: created } = await tasks.bulkLike(url);
      setBulkLikeTarget("");
      setBulkLikeMessage(
        testingMode
          ? `Created ${created.length} like task(s) — executing instantly! ⚡`
          : `Created ${created.length} like task(s) — spread over 24h.`
      );
      fetchData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Bulk like failed";
      setBulkLikeMessage(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setBulkLikeLoading(false);
    }
  };

  const handleBulkComment = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = bulkCommentTarget.trim();
    const msg = bulkCommentMessage.trim();
    if (!url || !msg) {
      setBulkCommentResult("Enter post/reel URL and comment text");
      return;
    }
    setError("");
    setBulkCommentResult("");
    setBulkCommentLoading(true);
    try {
      const { data: created } = await tasks.bulkComment(url, msg);
      setBulkCommentTarget("");
      setBulkCommentMessage("");
      setBulkCommentResult(
        testingMode
          ? `Created ${created.length} comment task(s) — executing instantly!`
          : `Created ${created.length} comment task(s) — spread over 24h.`
      );
      fetchData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Bulk comment failed";
      setBulkCommentResult(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setBulkCommentLoading(false);
    }
  };

  const handleBulkViewReel = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = bulkReelTarget.trim();
    if (!url) {
      setBulkReelMessage("Enter reel URL");
      return;
    }
    const perAccount = Math.max(1, Math.min(500, Number(bulkReelViewsPerAccount) || 1));
    setError("");
    setBulkReelMessage("");
    setBulkReelLoading(true);
    try {
      const { data: created } = await tasks.bulkViewReel(url, perAccount);
      setBulkReelTarget("");
      setBulkReelMessage(
        testingMode
          ? `Created ${created.length} view task(s) (${perAccount} per account).`
          : `Created ${created.length} view task(s) (${perAccount} per account) — spread over 24h.`
      );
      fetchData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Bulk view reel failed";
      setBulkReelMessage(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setBulkReelLoading(false);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Automation</h1>
          <p className="mt-1 text-slate-600">Create and manage automation tasks</p>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          <span className="text-sm font-medium text-slate-700">Testing mode</span>
          <button
            type="button"
            role="switch"
            aria-checked={testingMode}
            disabled={testingModeLoading}
            onClick={() => handleTestingModeToggle(!testingMode)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-60 ${testingMode ? "bg-primary-600" : "bg-slate-200"
              }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition ${testingMode ? "translate-x-5" : "translate-x-1"
                }`}
            />
          </button>
          <span className="text-xs text-slate-600">
            {testingMode ? "ON – limits bypassed" : "OFF – anti-ban active"}
          </span>
        </div>
      </div>
      {testingMode && (
        <p className="mt-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          Testing mode is on: warm-up, daily limits, and pause are skipped; delays are short. Use only for testing. Turn OFF for real use.
        </p>
      )}

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Follow with all accounts</h2>
        <p className="mt-1 text-sm text-slate-600">Create one follow task per account; tasks are spread over 24h to reduce detection risk.</p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleBulkFollow}>
          <div className="min-w-[200px]">
            <label className="block text-sm font-medium text-slate-700">Username to follow</label>
            <input
              type="text"
              value={bulkTarget}
              onChange={(e) => setBulkTarget(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="@username or username"
            />
          </div>
          <button
            type="submit"
            disabled={bulkLoading || accountList.length === 0}
            className="rounded-lg bg-slate-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {bulkLoading ? "Creating…" : "Follow with all accounts"}
          </button>
          {bulkMessage && <p className="text-sm text-slate-600">{bulkMessage}</p>}
        </form>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">❤️ Like with all accounts</h2>
        <p className="mt-1 text-sm text-slate-600">
          {testingMode
            ? "Testing mode ON — all likes will fire instantly ⚡"
            : "Create one like task per account; tasks are spread over 24h to reduce detection risk."}
        </p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleBulkLike}>
          <div className="min-w-[300px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Post URL</label>
            <input
              type="text"
              value={bulkLikeTarget}
              onChange={(e) => setBulkLikeTarget(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="https://www.instagram.com/p/... or reel URL"
            />
          </div>
          <button
            type="submit"
            disabled={bulkLikeLoading || accountList.length === 0}
            className="rounded-lg bg-gradient-to-r from-pink-500 to-red-500 px-4 py-2.5 text-sm font-medium text-white hover:from-pink-600 hover:to-red-600 disabled:opacity-60"
          >
            {bulkLikeLoading ? "Creating…" : "❤️ Like with all accounts"}
          </button>
          {bulkLikeMessage && <p className="text-sm text-slate-600">{bulkLikeMessage}</p>}
        </form>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">💬 Comment with all accounts</h2>
        <p className="mt-1 text-sm text-slate-600">
          Create one comment task per account for the same post/reel. Tasks are spread over 24h (or instant in testing mode).
        </p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleBulkComment}>
          <div className="min-w-[280px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Post or reel URL</label>
            <input
              type="text"
              value={bulkCommentTarget}
              onChange={(e) => setBulkCommentTarget(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="https://www.instagram.com/p/... or /reel/..."
            />
          </div>
          <div className="min-w-[200px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Comment text</label>
            <input
              type="text"
              value={bulkCommentMessage}
              onChange={(e) => setBulkCommentMessage(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Nice post! 🔥"
            />
          </div>
          <button
            type="submit"
            disabled={bulkCommentLoading || accountList.length === 0}
            className="rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-60"
          >
            {bulkCommentLoading ? "Creating…" : "💬 Comment with all accounts"}
          </button>
          {bulkCommentResult && <p className="w-full text-sm text-slate-600">{bulkCommentResult}</p>}
        </form>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">▶️ Increase reel views</h2>
        <p className="mt-1 text-sm text-slate-600">
          Create view tasks per account. &quot;Views per account&quot; = how many times each account will watch the reel (e.g. 10 = 10 views per account). Spread over 24h (or instant in testing mode).
        </p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleBulkViewReel}>
          <div className="min-w-[280px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Reel URL</label>
            <input
              type="text"
              value={bulkReelTarget}
              onChange={(e) => setBulkReelTarget(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="https://www.instagram.com/reel/..."
            />
          </div>
          <div className="min-w-[120px]">
            <label className="block text-sm font-medium text-slate-700">Views per account</label>
            <input
              type="number"
              min={1}
              max={500}
              value={bulkReelViewsPerAccount}
              onChange={(e) => setBulkReelViewsPerAccount(Number(e.target.value) || 1)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
          <button
            type="submit"
            disabled={bulkReelLoading || accountList.length === 0}
            className="rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-60"
          >
            {bulkReelLoading ? "Creating…" : "▶️ View reel with all accounts"}
          </button>
          {bulkReelMessage && <p className="w-full text-sm text-slate-600">{bulkReelMessage}</p>}
        </form>
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Create task (single account)</h2>
        <form className="mt-4 space-y-4" onSubmit={handleCreate}>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Account</label>
              <select
                value={form.account_id}
                onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                required
              >
                <option value="">Select account</option>
                {accountList.map((a) => (
                  <option key={a.id} value={a.id}>@{a.username}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Type</label>
              <select
                value={form.task_type}
                onChange={(e) => setForm((f) => ({ ...f, task_type: e.target.value }))}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                {TASK_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Target (URL or username)
              </label>
              <input
                type="text"
                value={form.target}
                onChange={(e) => setForm((f) => ({ ...f, target: e.target.value }))}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="https://... or username"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Scheduled (optional)</label>
              <input
                type="datetime-local"
                value={form.scheduled_time}
                onChange={(e) => setForm((f) => ({ ...f, scheduled_time: e.target.value }))}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
          </div>
          {(form.task_type === "SEND_DM" || form.task_type === "COMMENT_POST") && (
            <div>
              <label className="block text-sm font-medium text-slate-700">Message</label>
              <input
                type="text"
                value={form.message}
                onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
                className="mt-1 block w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="Your message"
              />
            </div>
          )}
          <button
            type="submit"
            disabled={creating || accountList.length === 0}
            className="rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
          >
            {creating ? "Creating…" : "Create task"}
          </button>
        </form>
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-200 px-6 py-4 text-lg font-medium text-slate-900">
          Tasks
        </h2>
        <TaskTable tasks={taskList} loading={loading} onDelete={handleDelete} />
      </div>
    </div>
  );
}
