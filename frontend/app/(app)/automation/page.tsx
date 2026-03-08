"use client";

import { useEffect, useState } from "react";
import { accounts, tasks, type Account, type Task } from "@/lib/api";
import TaskTable from "@/components/TaskTable";

const TASK_TYPES = [
  { value: "FOLLOW_USER", label: "Follow user" },
  { value: "COMMENT_POST", label: "Comment" },
  { value: "LIKE_POST", label: "Like post" },
  { value: "SEND_DM", label: "Send DM" },
  { value: "UPLOAD_POST", label: "Upload post" },
];

export default function AutomationPage() {
  const [taskList, setTaskList] = useState<Task[]>([]);
  const [accountList, setAccountList] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
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
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

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

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Automation</h1>
      <p className="mt-1 text-slate-600">Create and manage automation tasks</p>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Create task</h2>
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
