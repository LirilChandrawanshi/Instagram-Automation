"use client";

import { useEffect, useState } from "react";
import { analytics, type CommentDmEvent } from "@/lib/api";

export default function CommentDmPage() {
  const [totalSent, setTotalSent] = useState<number>(0);
  const [recent, setRecent] = useState<CommentDmEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    analytics
      .commentDm(50)
      .then((res) => {
        setTotalSent(res.data.total_sent);
        setRecent(res.data.recent ?? []);
      })
      .catch(() => {
        setTotalSent(0);
        setRecent([]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Comment-to-DM</h1>
      <p className="mt-1 text-slate-600">
        Stats and recent events for keyword → Private Reply (DM) automation
      </p>

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Total DMs sent (all time)</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {loading ? "—" : totalSent}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Recent events (last 50)</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {loading ? "—" : recent.length}
          </p>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-200 px-6 py-4 text-lg font-medium text-slate-900">
          Recent Comment-to-DM events
        </h2>
        {loading ? (
          <p className="p-6 text-slate-500">Loading…</p>
        ) : recent.length === 0 ? (
          <p className="p-6 text-slate-500">No events yet. Enable Comment-to-DM on posts and connect webhooks.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-500">Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-500">Comment</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-500">Media ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-slate-500">Comment ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {recent.map((ev) => (
                  <tr key={ev.comment_id}>
                    <td className="whitespace-nowrap px-6 py-3 text-sm text-slate-600">
                      {ev.created_at ? new Date(ev.created_at).toLocaleString() : "—"}
                    </td>
                    <td className="max-w-xs truncate px-6 py-3 text-sm text-slate-900" title={ev.comment_text}>
                      {ev.comment_text || "—"}
                    </td>
                    <td className="whitespace-nowrap px-6 py-3 text-sm text-slate-600">{ev.media_id || "—"}</td>
                    <td className="whitespace-nowrap px-6 py-3 text-xs text-slate-500">{ev.comment_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
