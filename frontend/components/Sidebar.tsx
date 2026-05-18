"use client";

import { useEffect, useState, useCallback } from "react";
import { getSessions, clearHistory } from "@/lib/api";
import { SessionInfo } from "@/lib/types";

type Props = {
  open: boolean;
  currentSessionId?: string;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
};

export default function Sidebar({ open, currentSessionId, onNewChat, onSelectSession, onDeleteSession }: Props) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [search, setSearch] = useState("");
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set();
    try { return new Set(JSON.parse(localStorage.getItem("pinnedSessions") || "[]")); } catch { return new Set(); }
  });

  const togglePinSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setPinnedIds((prev) => {
      const next = new Set(prev);
      next.has(sessionId) ? next.delete(sessionId) : next.add(sessionId);
      localStorage.setItem("pinnedSessions", JSON.stringify([...next]));
      return next;
    });
  };

  const refresh = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data.sessions);
    } catch {
      // backend not running yet — silently ignore
    }
  }, []);

  useEffect(() => {
    if (open) refresh();
  }, [open, currentSessionId, refresh]);

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // don't trigger onSelectSession
    try {
      await clearHistory(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      onDeleteSession(sessionId);
    } catch {
      // ignore
    }
  };

  return (
    <div className={`shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${open ? "w-64" : "w-0"}`}>
      <div className="w-64 h-full bg-slate-100 dark:bg-slate-900 flex flex-col border-r border-slate-200 dark:border-slate-700">

        {/* Header */}
        <div className="px-4 pt-5 pb-3 border-b border-slate-200 dark:border-slate-700">
          <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
            Conversations
          </p>
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-600 hover:bg-slate-700 text-white text-sm font-medium transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Search */}
        {sessions.length > 0 && (
          <div className="px-3 pb-3">
            <div className="flex items-center gap-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-1.5">
              <svg className="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search conversations..."
                className="flex-1 text-xs bg-transparent text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none"
              />
              {search && (
                <button onClick={() => setSearch("")} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-1">
          {sessions.length === 0 ? (
            <p className="text-xs text-slate-400 dark:text-slate-500 text-center mt-6 px-4">
              No conversations yet. Start chatting!
            </p>
          ) : (() => {
            const filtered = sessions.filter((s) =>
              !search.trim() ||
              s.title?.toLowerCase().includes(search.toLowerCase()) ||
              s.preview?.toLowerCase().includes(search.toLowerCase())
            );
            const pinned = filtered.filter((s) => pinnedIds.has(s.session_id));
            const recent = filtered.filter((s) => !pinnedIds.has(s.session_id));

            const renderSession = (s: SessionInfo) => (
              <div
                key={s.session_id}
                className={`group flex items-center gap-1 rounded-xl transition-colors ${
                  s.session_id === currentSessionId
                    ? "bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-slate-100"
                }`}
              >
                <button
                  onClick={() => onSelectSession(s.session_id)}
                  className="flex-1 text-left px-3 py-2.5 overflow-hidden"
                >
                  <div className="flex items-center gap-2">
                    {pinnedIds.has(s.session_id) ? (
                      <svg className="w-3.5 h-3.5 shrink-0 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M16 12V4h1a1 1 0 000-2H7a1 1 0 000 2h1v8l-2 2v2h5v5l1 1 1-1v-5h5v-2l-2-2z" />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5 shrink-0 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    )}
                    <p className="text-xs font-medium truncate">{s.title}</p>
                  </div>
                </button>
                <button
                  onClick={(e) => togglePinSession(e, s.session_id)}
                  title={pinnedIds.has(s.session_id) ? "Unpin" : "Pin conversation"}
                  className={`shrink-0 p-1 rounded opacity-0 group-hover:opacity-100 transition-all ${
                    pinnedIds.has(s.session_id)
                      ? "text-amber-500 hover:text-amber-600"
                      : "text-slate-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950"
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill={pinnedIds.has(s.session_id) ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M16 12V4h1a1 1 0 000-2H7a1 1 0 000 2h1v8l-2 2v2h5v5l1 1 1-1v-5h5v-2l-2-2z" />
                  </svg>
                </button>
                <button
                  onClick={(e) => handleDelete(e, s.session_id)}
                  title="Delete conversation"
                  className="shrink-0 mr-2 p-1 rounded opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-all"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            );

            return (
              <>
                {pinned.length > 0 && (
                  <>
                    <p className="text-xs font-semibold text-amber-500 dark:text-amber-400 uppercase tracking-wider px-2 pt-1 pb-1">
                      Pinned
                    </p>
                    {pinned.map(renderSession)}
                    {recent.length > 0 && <div className="border-t border-slate-200 dark:border-slate-700 my-1" />}
                  </>
                )}
                {recent.length > 0 && (
                  <>
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-2 pt-1 pb-1">
                      Recent
                    </p>
                    {recent.map(renderSession)}
                  </>
                )}
              </>
            );
          })()}
        </div>


</div>
    </div>
  );
}
