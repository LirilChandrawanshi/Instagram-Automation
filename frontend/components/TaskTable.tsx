"use client";

import { type Task } from "@/lib/api";

/** Parse API datetime (UTC, maybe without "Z") and format in user's local time. */
function formatLocal(isoOrNull: string | null | undefined): string {
  if (!isoOrNull) return "—";
  const utc = isoOrNull.endsWith("Z") ? isoOrNull : isoOrNull + "Z";
  return new Date(utc).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });
}

interface TaskTableProps {
  tasks: Task[];
  loading?: boolean;
  onDelete: (id: string) => void;
}

const taskTypeLabels: Record<string, string> = {
  LIKE_POST: "Like post",
  FOLLOW_USER: "Follow user",
  SEND_DM: "Send DM",
  COMMENT_POST: "Comment",
  UPLOAD_POST: "Upload post",
  VIEW_REEL: "View reel",
};

const statusColors: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  running: "bg-blue-100 text-blue-800",
  completed: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
};

export default function TaskTable({ tasks, loading, onDelete }: TaskTableProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <p className="py-12 text-center text-slate-500">No tasks yet. Create one above.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead>
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              Account
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              Target
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              Result / Message
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              Scheduled
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {tasks.map((task) => (
            <tr key={task.id}>
              <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-slate-900">
                {task.account_username ? `@${task.account_username}` : task.account_id || "—"}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-slate-900">
                {taskTypeLabels[task.task_type] ?? task.task_type}
              </td>
              <td className="max-w-[200px] truncate px-6 py-4 text-sm text-slate-600">
                {task.target || "—"}
              </td>
              <td className="whitespace-nowrap px-6 py-4">
                <span
                  className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    statusColors[task.status] ?? "bg-slate-100 text-slate-800"
                  }`}
                >
                  {task.status}
                </span>
              </td>
              <td className="max-w-[240px] px-6 py-4 text-sm text-slate-600">
                {task.result_message ??
                  (task.status === "failed" && task.payload && typeof task.payload.error === "string"
                    ? task.payload.error
                    : null) ?? "—"}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-500">
                {task.scheduled_time ? formatLocal(task.scheduled_time) : "ASAP"}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                <button
                  type="button"
                  onClick={() => onDelete(task.id)}
                  className="font-medium text-red-600 hover:text-red-700"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
