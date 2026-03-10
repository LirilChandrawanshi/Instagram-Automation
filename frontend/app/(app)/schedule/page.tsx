"use client";

import { useEffect, useState } from "react";
import { accounts, tasks, type Account } from "@/lib/api";

interface ScheduleItem {
  scheduled_time: string;
  media_type: "image" | "video";
  file: File | null;
  media_path: string | null;
  media_url: string;
  caption: string;
}

const defaultItem = (): ScheduleItem => ({
  scheduled_time: "",
  media_type: "image",
  file: null,
  media_path: null,
  media_url: "",
  caption: "",
});

export default function SchedulePage() {
  const [accountList, setAccountList] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState("");
  const [items, setItems] = useState<ScheduleItem[]>([defaultItem()]);
  const [uploading, setUploading] = useState(false);
  const [scheduling, setScheduling] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    accounts.list().then((res) => {
      setAccountList(res.data ?? []);
      if (res.data?.length && !accountId) setAccountId(res.data[0].id);
    }).catch(() => setAccountList([]));
  }, [accountId]);

  const addRow = () => setItems((prev) => [...prev, defaultItem()]);
  const removeRow = (i: number) => setItems((prev) => prev.filter((_, idx) => idx !== i));
  const updateItem = (i: number, upd: Partial<ScheduleItem>) => {
    setItems((prev) => prev.map((it, idx) => (idx === i ? { ...it, ...upd } : it)));
  };

  const uploadFile = async (i: number) => {
    const item = items[i];
    if (!item.file) {
      setError("Choose a file first");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const { data } = await tasks.uploadMedia(item.file);
      updateItem(i, { media_path: data.media_path, media_url: "" });
      setMessage(`Uploaded: ${item.file.name}`);
    } catch {
      setError("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleBulkSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountId) {
      setError("Select an account");
      return;
    }
    const valid = items.filter(
      (it) => (it.media_path || it.media_url) && it.scheduled_time
    );
    if (!valid.length) {
      setError("Add at least one item with date/time and media (upload file or paste URL).");
      return;
    }
    setScheduling(true);
    setError("");
    setMessage("");
    try {
      const payload = {
        account_id: accountId,
        items: valid.map((it) => ({
          scheduled_time: new Date(it.scheduled_time).toISOString(),
          media_type: it.media_type,
          media_path: it.media_path || undefined,
          media_url: it.media_url || undefined,
          caption: it.caption || "",
        })),
      };
      const { data: created } = await tasks.bulkSchedulePosts(payload);
      setMessage(`Scheduled ${created.length} post(s)/reel(s).`);
      setItems([defaultItem()]);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Schedule failed";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setScheduling(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Schedule posts & reels</h1>
      <p className="mt-1 text-slate-600">
        Upload images or videos and bulk-schedule them. Each item runs at its scheduled time.
      </p>

      <form onSubmit={handleBulkSchedule} className="mt-8 space-y-6">
        {error && <p className="text-sm text-red-600">{error}</p>}
        {message && <p className="text-sm text-emerald-600">{message}</p>}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-medium text-slate-700">Account</label>
          <select
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            className="mt-1 block w-full max-w-xs rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            <option value="">Select account</option>
            {accountList.map((a) => (
              <option key={a.id} value={a.id}>@{a.username}</option>
            ))}
          </select>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-slate-900">Scheduled items</h2>
            <button
              type="button"
              onClick={addRow}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              + Add row
            </button>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            Upload a file (image or video) or paste a public media URL. Set date/time for each item.
          </p>
          <div className="mt-4 space-y-4">
            {items.map((item, i) => (
              <div
                key={i}
                className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-slate-50/50 p-4"
              >
                <div className="min-w-[180px]">
                  <label className="block text-xs font-medium text-slate-500">Date & time</label>
                  <input
                    type="datetime-local"
                    value={item.scheduled_time}
                    onChange={(e) => updateItem(i, { scheduled_time: e.target.value })}
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                  />
                </div>
                <div className="min-w-[100px]">
                  <label className="block text-xs font-medium text-slate-500">Type</label>
                  <select
                    value={item.media_type}
                    onChange={(e) => updateItem(i, { media_type: e.target.value as "image" | "video" })}
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                  >
                    <option value="image">Image (post)</option>
                    <option value="video">Video (reel)</option>
                  </select>
                </div>
                <div className="min-w-[160px]">
                  <label className="block text-xs font-medium text-slate-500">File</label>
                  <input
                    type="file"
                    accept={item.media_type === "video" ? "video/*" : "image/*"}
                    onChange={(e) => updateItem(i, { file: e.target.files?.[0] ?? null, media_path: null })}
                    className="mt-1 block w-full text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => uploadFile(i)}
                    disabled={uploading || !item.file}
                    className="mt-1 rounded bg-slate-600 px-2 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50"
                  >
                    {uploading ? "Uploading…" : "Upload"}
                  </button>
                </div>
                <div className="min-w-[200px] flex-1">
                  <label className="block text-xs font-medium text-slate-500">Or media URL</label>
                  <input
                    type="text"
                    value={item.media_url}
                    onChange={(e) => updateItem(i, { media_url: e.target.value })}
                    placeholder="https://..."
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                  />
                </div>
                <div className="min-w-[180px] flex-1">
                  <label className="block text-xs font-medium text-slate-500">Caption</label>
                  <input
                    type="text"
                    value={item.caption}
                    onChange={(e) => updateItem(i, { caption: e.target.value })}
                    placeholder="Caption..."
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                  />
                </div>
                {item.media_path && (
                  <span className="text-xs text-slate-500">✓ {item.media_path}</span>
                )}
                <button
                  type="button"
                  onClick={() => removeRow(i)}
                  className="rounded border border-red-200 px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={scheduling || accountList.length === 0}
          className="rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
        >
          {scheduling ? "Scheduling…" : "Schedule all"}
        </button>
      </form>
    </div>
  );
}
