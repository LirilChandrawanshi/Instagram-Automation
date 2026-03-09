"use client";

import { useEffect, useState } from "react";
import { instagramApi, settings } from "@/lib/api";

export default function InstagramApiPage() {
  const [dmUserId, setDmUserId] = useState("");
  const [dmMessage, setDmMessage] = useState("");
  const [dmLoading, setDmLoading] = useState(false);
  const [dmResult, setDmResult] = useState("");

  const [replyAll, setReplyAll] = useState(false);
  const [replyAllMessage, setReplyAllMessage] = useState("Thanks for commenting! We've sent you a message.");
  const [replyAllLoading, setReplyAllLoading] = useState(false);

  const [enabledPostIds, setEnabledPostIds] = useState<string[]>([]);
  const [newEnabledMediaId, setNewEnabledMediaId] = useState("");
  const [enabledPostsLoading, setEnabledPostsLoading] = useState(false);

  const [requireFollower, setRequireFollower] = useState(false);
  const [nonFollowerMessage, setNonFollowerMessage] = useState(
    "I think you're not following me! Please follow and comment again to get the link."
  );
  const [allowedUserIds, setAllowedUserIds] = useState<string[]>([]);
  const [newAllowedUserId, setNewAllowedUserId] = useState("");
  const [followerCheckLoading, setFollowerCheckLoading] = useState(false);

  const [mediaId, setMediaId] = useState("");
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [comments, setComments] = useState<Array<{ id: string; text: string; username?: string }>>([]);

  const [replyCommentId, setReplyCommentId] = useState("");
  const [replyMessage, setReplyMessage] = useState("");
  const [replyLoading, setReplyLoading] = useState(false);

  const [hideCommentId, setHideCommentId] = useState("");
  const [hideLoading, setHideLoading] = useState(false);

  const [deleteCommentId, setDeleteCommentId] = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    settings.getInstagramReplyAll().then((r) => {
      setReplyAll(r.data.reply_all);
      setReplyAllMessage(r.data.reply_all_message || "");
    }).catch(() => {});
  }, []);

  useEffect(() => {
    settings.getCommentDmEnabledPosts().then((r) => setEnabledPostIds(r.data.media_ids || [])).catch(() => {});
  }, []);

  useEffect(() => {
    settings.getInstagramFollowerCheck().then((r) => {
      setRequireFollower(r.data.require_follower);
      setNonFollowerMessage(r.data.non_follower_message || "I think you're not following me! Please follow and comment again to get the link.");
    }).catch(() => {});
  }, []);

  useEffect(() => {
    settings.getInstagramDmAllowedUsers().then((r) => setAllowedUserIds(r.data.user_ids || [])).catch(() => {});
  }, []);

  const handleFollowerCheckToggle = async (on: boolean) => {
    setFollowerCheckLoading(true);
    setError("");
    try {
      const r = await settings.setInstagramFollowerCheck(on, nonFollowerMessage);
      setRequireFollower(r.data.require_follower);
      setNonFollowerMessage(r.data.non_follower_message || "");
    } catch {
      setError("Failed to update follower check");
    } finally {
      setFollowerCheckLoading(false);
    }
  };

  const handleSaveFollowerCheckMessage = async () => {
    setFollowerCheckLoading(true);
    setError("");
    try {
      const r = await settings.setInstagramFollowerCheck(requireFollower, nonFollowerMessage);
      setNonFollowerMessage(r.data.non_follower_message || "");
    } catch {
      setError("Failed to save message");
    } finally {
      setFollowerCheckLoading(false);
    }
  };

  const handleAddAllowedUser = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = newAllowedUserId.trim();
    if (!id) return;
    setError("");
    setFollowerCheckLoading(true);
    try {
      const r = await settings.addInstagramDmAllowedUser(id);
      setAllowedUserIds(r.data.user_ids || []);
      setNewAllowedUserId("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to add user";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setFollowerCheckLoading(false);
    }
  };

  const handleRemoveAllowedUser = async (uid: string) => {
    setError("");
    setFollowerCheckLoading(true);
    try {
      const r = await settings.removeInstagramDmAllowedUser(uid);
      setAllowedUserIds(r.data.user_ids || []);
    } catch {
      setError("Failed to remove user");
    } finally {
      setFollowerCheckLoading(false);
    }
  };

  const handleAddEnabledPost = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = newEnabledMediaId.trim();
    if (!id) return;
    setError("");
    setEnabledPostsLoading(true);
    try {
      const r = await settings.addCommentDmEnabledPost(id);
      setEnabledPostIds(r.data.media_ids || []);
      setNewEnabledMediaId("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to add post";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setEnabledPostsLoading(false);
    }
  };

  const handleRemoveEnabledPost = async (mediaIdToRemove: string) => {
    setError("");
    setEnabledPostsLoading(true);
    try {
      const r = await settings.removeCommentDmEnabledPost(mediaIdToRemove);
      setEnabledPostIds(r.data.media_ids || []);
    } catch {
      setError("Failed to remove post");
    } finally {
      setEnabledPostsLoading(false);
    }
  };

  const handleReplyAllToggle = async (on: boolean) => {
    setReplyAllLoading(true);
    setError("");
    try {
      const r = await settings.setInstagramReplyAll(on, replyAllMessage);
      setReplyAll(r.data.reply_all);
      setReplyAllMessage(r.data.reply_all_message || "");
    } catch {
      setError("Failed to update reply-all setting");
    } finally {
      setReplyAllLoading(false);
    }
  };

  const handleSendDm = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setDmResult("");
    setDmLoading(true);
    try {
      await instagramApi.sendDm(dmUserId.trim(), dmMessage.trim());
      setDmResult("Message sent.");
      setDmMessage("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to send DM";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setDmLoading(false);
    }
  };

  const handleGetComments = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setComments([]);
    setCommentsLoading(true);
    try {
      const res = await instagramApi.getComments(mediaId.trim());
      setComments(res.data?.data ?? []);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to get comments";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setCommentsLoading(false);
    }
  };

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setReplyLoading(true);
    try {
      await instagramApi.replyToComment(replyCommentId.trim(), replyMessage.trim());
      setReplyMessage("");
      setReplyCommentId("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to reply";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setReplyLoading(false);
    }
  };

  const handleHide = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setHideLoading(true);
    try {
      await instagramApi.hideComment(hideCommentId.trim());
      setHideCommentId("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to hide comment";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setHideLoading(false);
    }
  };

  const handleDelete = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setDeleteLoading(true);
    try {
      await instagramApi.deleteComment(deleteCommentId.trim());
      setDeleteCommentId("");
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to delete comment";
      setError(Array.isArray(msg) ? msg[0] : String(msg));
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Instagram API</h1>
      <p className="mt-1 text-slate-600">
        Direct Messages and Comments via official Instagram Graph API (Business/Creator account)
      </p>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Reply to all comments */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Reply to all comments</h2>
        <p className="mt-1 text-sm text-slate-600">
          When ON, every new comment gets an automatic Private Reply (DM) with the message below. When OFF, only comments matching keywords (e.g. LINK, EBOOK) get a reply.
        </p>
        <div className="mt-4 flex flex-wrap items-end gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={replyAll}
              disabled={replyAllLoading}
              onClick={() => handleReplyAllToggle(!replyAll)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-60 ${
                replyAll ? "bg-primary-600" : "bg-slate-200"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition ${
                  replyAll ? "translate-x-5" : "translate-x-1"
                }`}
              />
            </button>
            <span className="text-sm text-slate-700">{replyAll ? "ON – replying to every comment" : "OFF – keyword only"}</span>
          </div>
          <div className="min-w-[280px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Message sent in DM for each comment</label>
            <input
              type="text"
              value={replyAllMessage}
              onChange={(e) => setReplyAllMessage(e.target.value)}
              onBlur={() => replyAll && handleReplyAllToggle(true)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Thanks for commenting! We've sent you a message."
            />
          </div>
          <button
            type="button"
            onClick={() => handleReplyAllToggle(replyAll)}
            disabled={replyAllLoading}
            className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
          >
            Save message
          </button>
        </div>
      </div>

      {/* Auto-reply on these posts */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Auto-reply on these posts</h2>
        <p className="mt-1 text-sm text-slate-600">
          Only comments on these posts will get an automatic DM. Add the post&apos;s Media ID (get it from &quot;Get comments&quot; below for a post).
        </p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleAddEnabledPost}>
          <div className="min-w-[240px]">
            <label className="block text-sm font-medium text-slate-700">Media ID (post ID)</label>
            <input
              type="text"
              value={newEnabledMediaId}
              onChange={(e) => setNewEnabledMediaId(e.target.value)}
              placeholder="e.g. 12345678901234567"
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
          <button
            type="submit"
            disabled={enabledPostsLoading || !newEnabledMediaId.trim()}
            className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
          >
            Add post
          </button>
        </form>
        {enabledPostIds.length > 0 && (
          <ul className="mt-4 space-y-2">
            {enabledPostIds.map((mid) => (
              <li key={mid} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <span className="font-mono text-slate-700">{mid}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveEnabledPost(mid)}
                  disabled={enabledPostsLoading}
                  className="text-red-600 hover:underline disabled:opacity-60"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Only send link to followers */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Only send link to followers</h2>
        <p className="mt-1 text-sm text-slate-600">
          When ON, only users in the &quot;Allowed users&quot; list below get the link in DMs. Everyone else gets the &quot;Non-follower message&quot; (e.g. &quot;I think you&apos;re not following me!&quot;). Add Instagram User IDs to the list (e.g. from webhook or comment data). Instagram API does not provide a followers list, so you maintain this list manually or via another tool.
        </p>
        <div className="mt-4 flex flex-wrap items-end gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={requireFollower}
              disabled={followerCheckLoading}
              onClick={() => handleFollowerCheckToggle(!requireFollower)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-60 ${
                requireFollower ? "bg-primary-600" : "bg-slate-200"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition ${
                  requireFollower ? "translate-x-5" : "translate-x-1"
                }`}
              />
            </button>
            <span className="text-sm text-slate-700">{requireFollower ? "ON – only allowed users get the link" : "OFF – everyone gets the link"}</span>
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-slate-700">Non-follower message (DM when user is not in the list)</label>
          <input
            type="text"
            value={nonFollowerMessage}
            onChange={(e) => setNonFollowerMessage(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
            placeholder="I think you're not following me! Please follow and comment again to get the link."
          />
          <button
            type="button"
            onClick={handleSaveFollowerCheckMessage}
            disabled={followerCheckLoading}
            className="mt-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
          >
            Save message
          </button>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-slate-700">Allowed users (Instagram User IDs that get the link)</label>
          <form className="mt-2 flex flex-wrap items-end gap-3" onSubmit={handleAddAllowedUser}>
            <input
              type="text"
              value={newAllowedUserId}
              onChange={(e) => setNewAllowedUserId(e.target.value)}
              placeholder="e.g. 12345678901234567"
              className="block w-64 rounded-lg border border-slate-300 px-3 py-2"
            />
            <button
              type="submit"
              disabled={followerCheckLoading || !newAllowedUserId.trim()}
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
            >
              Add user
            </button>
          </form>
          {allowedUserIds.length > 0 && (
            <ul className="mt-3 space-y-2">
              {allowedUserIds.map((uid) => (
                <li key={uid} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  <span className="font-mono text-slate-700">{uid}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveAllowedUser(uid)}
                    disabled={followerCheckLoading}
                    className="text-red-600 hover:underline disabled:opacity-60"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Webhook info */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-slate-50 p-6">
        <h2 className="text-lg font-medium text-slate-900">Webhook</h2>
        <p className="mt-1 text-sm text-slate-600">
          Configure in Meta Developer: GET and POST to <code className="rounded bg-slate-200 px-1">/webhooks/instagram</code>.
          Set INSTAGRAM_VERIFY_TOKEN in .env for verification.
        </p>
      </div>

      {/* Send DM */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Send Direct Message</h2>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleSendDm}>
          <div className="min-w-[180px]">
            <label className="block text-sm font-medium text-slate-700">Instagram User ID</label>
            <input
              type="text"
              value={dmUserId}
              onChange={(e) => setDmUserId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="e.g. 123456789"
              required
            />
          </div>
          <div className="min-w-[200px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Message</label>
            <input
              type="text"
              value={dmMessage}
              onChange={(e) => setDmMessage(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Hello! How can we help?"
              required
            />
          </div>
          <button
            type="submit"
            disabled={dmLoading}
            className="rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
          >
            {dmLoading ? "Sending…" : "Send DM"}
          </button>
        </form>
        {dmResult && <p className="mt-2 text-sm text-emerald-600">{dmResult}</p>}
      </div>

      {/* Get comments */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Get post comments</h2>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleGetComments}>
          <div className="min-w-[280px]">
            <label className="block text-sm font-medium text-slate-700">Media ID (from Graph API)</label>
            <input
              type="text"
              value={mediaId}
              onChange={(e) => setMediaId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="e.g. 17889455560051444"
              required
            />
          </div>
          <button
            type="submit"
            disabled={commentsLoading}
            className="rounded-lg bg-slate-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {commentsLoading ? "Loading…" : "Get comments"}
          </button>
        </form>
        {comments.length > 0 && (
          <ul className="mt-4 space-y-2">
            {comments.map((c) => (
              <li key={c.id} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <span className="font-mono text-slate-500">{c.id}</span> — {c.text}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Reply to comment */}
      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Reply to comment</h2>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleReply}>
          <div className="min-w-[200px]">
            <label className="block text-sm font-medium text-slate-700">Comment ID</label>
            <input
              type="text"
              value={replyCommentId}
              onChange={(e) => setReplyCommentId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Comment ID"
              required
            />
          </div>
          <div className="min-w-[200px] flex-1">
            <label className="block text-sm font-medium text-slate-700">Reply message</label>
            <input
              type="text"
              value={replyMessage}
              onChange={(e) => setReplyMessage(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Thank you!"
              required
            />
          </div>
          <button
            type="submit"
            disabled={replyLoading}
            className="rounded-lg bg-slate-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {replyLoading ? "Sending…" : "Reply"}
          </button>
        </form>
      </div>

      {/* Hide / Delete comment */}
      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-medium text-slate-900">Hide comment</h2>
          <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleHide}>
            <div className="min-w-[180px] flex-1">
              <label className="block text-sm font-medium text-slate-700">Comment ID</label>
              <input
                type="text"
                value={hideCommentId}
                onChange={(e) => setHideCommentId(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
                required
              />
            </div>
            <button
              type="submit"
              disabled={hideLoading}
              className="rounded-lg bg-amber-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-60"
            >
              {hideLoading ? "Hiding…" : "Hide"}
            </button>
          </form>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-medium text-slate-900">Delete comment</h2>
          <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleDelete}>
            <div className="min-w-[180px] flex-1">
              <label className="block text-sm font-medium text-slate-700">Comment ID</label>
              <input
                type="text"
                value={deleteCommentId}
                onChange={(e) => setDeleteCommentId(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2"
                required
              />
            </div>
            <button
              type="submit"
              disabled={deleteLoading}
              className="rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
            >
              {deleteLoading ? "Deleting…" : "Delete"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
