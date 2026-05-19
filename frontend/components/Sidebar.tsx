"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { getSessions, clearHistory, renameSession } from "@/lib/api";
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

  const [renamedTitles, setRenamedTitles] = useState<Record<string, string>>(() => {
    if (typeof window === "undefined") return {};
    try { return JSON.parse(localStorage.getItem("renamedTitles") || "{}"); } catch { return {}; }
  });

  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const menuRef = useRef<HTMLDivElement>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  // Close menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Focus rename input when opened
  useEffect(() => {
    if (renamingId) renameInputRef.current?.focus();
  }, [renamingId]);

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

  const handleDelete = async (sessionId: string) => {
    setOpenMenuId(null);
    try {
      await clearHistory(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      onDeleteSession(sessionId);
    } catch {
      // ignore
    }
  };

  const handleTogglePin = (sessionId: string) => {
    setOpenMenuId(null);
    setPinnedIds((prev) => {
      const next = new Set(prev);
      next.has(sessionId) ? next.delete(sessionId) : next.add(sessionId);
      localStorage.setItem("pinnedSessions", JSON.stringify([...next]));
      return next;
    });
  };

  const startRename = (sessionId: string, currentTitle: string) => {
    setOpenMenuId(null);
    setRenamingId(sessionId);
    setRenameValue(renamedTitles[sessionId] || currentTitle);
  };

  const commitRename = async (sessionId: string) => {
    const trimmed = renameValue.trim();
    if (trimmed) {
      const updated = { ...renamedTitles, [sessionId]: trimmed };
      setRenamedTitles(updated);
      localStorage.setItem("renamedTitles", JSON.stringify(updated));
      try {
        await renameSession(sessionId, trimmed);
      } catch {
        // backend unavailable — localStorage rename still applies
      }
    }
    setRenamingId(null);
  };

  const renderSession = (s: SessionInfo) => {
    const displayTitle = renamedTitles[s.session_id] || s.title;
    const isPinned = pinnedIds.has(s.session_id);
    const isMenuOpen = openMenuId === s.session_id;
    const isRenaming = renamingId === s.session_id;

    return (
      <div
        key={s.session_id}
        className={`group relative flex items-center rounded-xl transition-colors ${
          s.session_id === currentSessionId
            ? "bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-slate-100"
            : "text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-slate-100"
        }`}
      >
        {/* Session button or rename input */}
        {isRenaming ? (
          <input
            ref={renameInputRef}
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={() => commitRename(s.session_id)}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRename(s.session_id);
              if (e.key === "Escape") setRenamingId(null);
            }}
            className="flex-1 mx-2 my-1 px-2 py-1.5 text-xs rounded-lg bg-white dark:bg-slate-600 border border-slate-300 dark:border-slate-500 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-slate-500"
          />
        ) : (
          <button
            onClick={() => onSelectSession(s.session_id)}
            className="flex-1 text-left px-3 py-2.5 overflow-hidden"
          >
            <div className="flex items-center gap-2">
              {isPinned ? (
                <svg className="w-3.5 h-3.5 shrink-0 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16 12V4h1a1 1 0 000-2H7a1 1 0 000 2h1v8l-2 2v2h5v5l1 1 1-1v-5h5v-2l-2-2z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5 shrink-0 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              )}
              <p className="text-xs font-medium truncate">{displayTitle}</p>
            </div>
          </button>
        )}

        {/* Three-dot menu button */}
        {!isRenaming && (
          <div className="relative shrink-0 mr-1" ref={isMenuOpen ? menuRef : null}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setOpenMenuId(isMenuOpen ? null : s.session_id);
              }}
              title="More options"
              className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600 transition-all"
            >
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 13a1 1 0 100-2 1 1 0 000 2zm-5 0a1 1 0 100-2 1 1 0 000 2zm10 0a1 1 0 100-2 1 1 0 000 2z" />
              </svg>
            </button>

            {/* Dropdown menu */}
            {isMenuOpen && (
              <div className="absolute right-0 top-8 z-50 w-40 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 py-1 overflow-hidden">

                {/* Pin / Unpin */}
                <button
                  onClick={() => handleTogglePin(s.session_id)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <svg className="w-3.5 h-3.5 text-amber-500 shrink-0" fill={isPinned ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M16 12V4h1a1 1 0 000-2H7a1 1 0 000 2h1v8l-2 2v2h5v5l1 1 1-1v-5h5v-2l-2-2z" />
                  </svg>
                  {isPinned ? "Unpin" : "Pin"}
                </button>

                {/* Rename */}
                <button
                  onClick={() => startRename(s.session_id, displayTitle)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <svg className="w-3.5 h-3.5 text-slate-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Rename
                </button>

                <div className="border-t border-slate-200 dark:border-slate-700 my-1" />

                {/* Delete */}
                <button
                  onClick={() => handleDelete(s.session_id)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                >
                  <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete
                </button>

              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const filtered = sessions.filter((s) =>
    !search.trim() ||
    (renamedTitles[s.session_id] || s.title)?.toLowerCase().includes(search.toLowerCase()) ||
    s.preview?.toLowerCase().includes(search.toLowerCase())
  );
  const pinned = filtered.filter((s) => pinnedIds.has(s.session_id));
  const recent = filtered.filter((s) => !pinnedIds.has(s.session_id));

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
          <div className="px-3 pt-3 pb-2">
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
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
          {sessions.length === 0 ? (
            <p className="text-xs text-slate-400 dark:text-slate-500 text-center mt-6 px-4">
              No conversations yet. Start chatting!
            </p>
          ) : (
            <>
              {pinned.length > 0 && (
                <>
                  <p className="text-xs font-semibold text-amber-500 dark:text-amber-400 uppercase tracking-wider px-2 pt-1 pb-1">
                    Pinned
                  </p>
                  {pinned.map(renderSession)}
                  {recent.length > 0 && <div className="border-t border-slate-200 dark:border-slate-700 my-1.5" />}
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
          )}
        </div>

      </div>
    </div>
  );
}
