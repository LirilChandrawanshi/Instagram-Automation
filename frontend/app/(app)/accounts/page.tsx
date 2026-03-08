"use client";

import { useEffect, useState } from "react";
import { accounts, type Account } from "@/lib/api";

export default function AccountsPage() {
  const [list, setList] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [username, setUsername] = useState("");
  const [sessionCookie, setSessionCookie] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showGuide, setShowGuide] = useState(false);

  const fetchAccounts = () => {
    accounts
      .list()
      .then((res) => setList(res.data))
      .catch(() => setList([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setConnecting(true);
    try {
      if (!sessionCookie.trim()) {
        setError("Session cookies are required for automation. See the guide below.");
        setConnecting(false);
        return;
      }
      let cookiePayload: string | undefined;
      try {
        JSON.parse(sessionCookie.trim());
        cookiePayload = sessionCookie.trim();
      } catch {
        setError("Invalid JSON! Make sure you pasted the full cookie array from Cookie-Editor.");
        setConnecting(false);
        return;
      }
      await accounts.connect({ username, session_cookie: cookiePayload });
      setUsername("");
      setSessionCookie("");
      setSuccess(`@${username} connected successfully! 🎉`);
      fetchAccounts();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Failed to connect";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setConnecting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this account?")) return;
    try {
      await accounts.delete(id);
      fetchAccounts();
    } catch {
      setError("Failed to delete");
    }
  };

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-semibold text-slate-900">Accounts</h1>
      <p className="mt-1 text-slate-600">
        Connect your Instagram accounts to start automating
      </p>

      {/* ─── Connect Account Form ─── */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-lg text-white">
            +
          </div>
          <div>
            <h2 className="text-lg font-medium text-slate-900">
              Connect Instagram Account
            </h2>
            <p className="text-sm text-slate-500">
              Paste your Instagram cookies to connect your account
            </p>
          </div>
        </div>

        <form className="mt-6 space-y-5" onSubmit={handleConnect}>
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              ⚠️ {error}
            </div>
          )}
          {success && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {success}
            </div>
          )}

          {/* Username */}
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-slate-700"
            >
              Instagram Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2.5 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="e.g. your_insta_handle"
              required
            />
          </div>

          {/* Session Cookies */}
          <div>
            <div className="flex items-center justify-between">
              <label
                htmlFor="cookies"
                className="block text-sm font-medium text-slate-700"
              >
                Session Cookies (JSON)
              </label>
              <button
                type="button"
                onClick={() => setShowGuide(!showGuide)}
                className="text-xs font-medium text-primary-600 hover:text-primary-700"
              >
                {showGuide ? "Hide guide ▲" : "How to get cookies? ▼"}
              </button>
            </div>

            {/* Guide */}
            {showGuide && (
              <div className="mt-2 rounded-lg border border-primary-100 bg-primary-50/50 p-4 text-sm text-slate-700">
                <p className="font-medium text-primary-800 mb-2">
                  📋 How to get cookies (2 min):
                </p>
                <ol className="list-decimal list-inside space-y-1.5 text-slate-600">
                  <li>
                    Install{" "}
                    <span className="font-semibold text-slate-800">
                      Cookie-Editor
                    </span>{" "}
                    extension in Chrome
                  </li>
                  <li>
                    Open{" "}
                    <span className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">
                      instagram.com
                    </span>{" "}
                    and log in to your account
                  </li>
                  <li>Click the Cookie-Editor extension icon</li>
                  <li>
                    Click{" "}
                    <span className="font-semibold text-slate-800">
                      Export → JSON
                    </span>{" "}
                    (copies to clipboard)
                  </li>
                  <li>Paste below ↓</li>
                </ol>
                <p className="mt-2 text-xs text-slate-500">
                  🔒 Cookies are stored securely and used only for automation.
                  They expire periodically — reconnect when needed.
                </p>
              </div>
            )}

            <textarea
              id="cookies"
              rows={7}
              value={sessionCookie}
              onChange={(e) => setSessionCookie(e.target.value)}
              placeholder={'[\n  {"name":"sessionid","value":"...","domain":".instagram.com"},\n  ...\n]'}
              className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2.5 font-mono text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
            <p className="mt-1 text-xs text-slate-400">
              Paste the full JSON array exported from Cookie-Editor
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={connecting}
            className="w-full rounded-lg bg-gradient-to-r from-primary-600 to-primary-700 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:from-primary-700 hover:to-primary-800 disabled:opacity-60 sm:w-auto sm:px-8"
          >
            {connecting ? "Connecting…" : "🔗 Connect Account"}
          </button>
        </form>
      </div>

      {/* ─── Connected Accounts List ─── */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-200 px-6 py-4 text-lg font-medium text-slate-900">
          Connected Accounts
          {list.length > 0 && (
            <span className="ml-2 inline-flex items-center rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-medium text-primary-700">
              {list.length}
            </span>
          )}
        </h2>
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
          </div>
        ) : list.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-4xl">📱</p>
            <p className="mt-2 text-slate-500">
              No accounts connected yet. Add one above to get started!
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-200">
            {list.map((acc) => (
              <li
                key={acc.id}
                className="flex items-center justify-between px-6 py-4 transition-colors hover:bg-slate-50"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-pink-500 via-red-500 to-yellow-500 text-sm font-bold text-white">
                    {acc.username[0]?.toUpperCase() || "?"}
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">
                      @{acc.username}
                    </p>
                    <p className="text-xs text-slate-500">
                      <span
                        className={`mr-1 inline-block h-2 w-2 rounded-full ${acc.status === "connected"
                            ? "bg-emerald-400"
                            : acc.status === "error"
                              ? "bg-red-400"
                              : "bg-amber-400"
                          }`}
                      />
                      {acc.status}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(acc.id)}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
