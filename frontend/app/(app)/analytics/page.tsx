"use client";

import { useEffect, useState } from "react";
import { analytics } from "@/lib/api";
import AnalyticsCharts from "@/components/AnalyticsCharts";

export default function AnalyticsPage() {
  const [data, setData] = useState<{
    total_accounts: number;
    tasks_by_status: Record<string, number>;
    tasks_by_type: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    analytics.overview().then((res) => setData(res.data)).catch(() => setData(null));
  }, []);

  const tasksByStatus = data?.tasks_by_status ?? {};
  const tasksByType = data?.tasks_by_type ?? {};

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Analytics</h1>
      <p className="mt-1 text-slate-600">Task and account overview</p>

      <div className="mt-8 grid gap-6 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Total accounts</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {data?.total_accounts ?? "—"}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Total tasks</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {Object.values(tasksByStatus).reduce((a, b) => a + b, 0) || "—"}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Completed</p>
          <p className="mt-2 text-3xl font-semibold text-emerald-600">
            {tasksByStatus.completed ?? 0}
          </p>
        </div>
      </div>

      <AnalyticsCharts tasksByType={tasksByType} tasksByStatus={tasksByStatus} />
    </div>
  );
}
