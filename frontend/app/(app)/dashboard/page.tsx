"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { analytics } from "@/lib/api";

export default function DashboardPage() {
  const [data, setData] = useState<{
    total_accounts: number;
    tasks_by_status: Record<string, number>;
    tasks_by_type: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    analytics.overview().then((res) => setData(res.data)).catch(() => setData(null));
  }, []);

  const pending = data?.tasks_by_status?.pending ?? 0;
  const completed = data?.tasks_by_status?.completed ?? 0;
  const failed = data?.tasks_by_status?.failed ?? 0;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-slate-600">Overview of your automation</p>

      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          href="/accounts"
          className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
        >
          <p className="text-sm font-medium text-slate-500">Connected accounts</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {data?.total_accounts ?? "—"}
          </p>
        </Link>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Pending tasks</p>
          <p className="mt-2 text-3xl font-semibold text-amber-600">{pending}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Completed</p>
          <p className="mt-2 text-3xl font-semibold text-emerald-600">{completed}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Failed</p>
          <p className="mt-2 text-3xl font-semibold text-red-600">{failed}</p>
        </div>
      </div>

      <div className="mt-8 flex gap-4">
        <Link
          href="/accounts"
          className="rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-primary-700"
        >
          Connect account
        </Link>
        <Link
          href="/automation"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Create task
        </Link>
      </div>
    </div>
  );
}
