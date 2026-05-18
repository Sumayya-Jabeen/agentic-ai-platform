"use client";

import { useEffect, useState, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import ChatWindow from "@/components/ChatWindow";
import InputBar from "@/components/InputBar";
import Sidebar from "@/components/Sidebar";
import { healthCheck } from "@/lib/api";

type BackendStatus = "checking" | "online" | "offline";

export default function ChatPage() {
  const { messages, sessionId, isLoading, error, send, resendFromMessage, stop, togglePin, clear, loadSession } = useChat();
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [dark, setDark] = useState(false);
  const prevLoadingRef = useRef(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
    if (Notification.permission === "default") Notification.requestPermission();
  }, []);

  // Fire a browser notification when a response finishes while the tab is hidden
  useEffect(() => {
    if (prevLoadingRef.current && !isLoading && document.hidden) {
      if (Notification.permission === "granted") {
        new Notification("Agentic AI", {
          body: "Your response is ready.",
          icon: "/favicon.ico",
        });
      }
    }
    prevLoadingRef.current = isLoading;
  }, [isLoading]);

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  const exportConversation = () => {
    if (messages.length === 0) return;
    const lines = messages
      .filter((m) => !m.isLoading)
      .map((m) => {
        const role = m.role === "user" ? "You" : "Assistant";
        const time = m.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        return `## ${role} — ${time}\n\n${m.content}`;
      });
    const content = `# Conversation Export\n_Exported on ${new Date().toLocaleDateString()}_\n\n---\n\n${lines.join("\n\n---\n\n")}`;
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    healthCheck()
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">

      {/* ── Sidebar ── */}
      <Sidebar
        open={sidebarOpen}
        currentSessionId={sessionId}
        onNewChat={clear}
        onSelectSession={loadSession}
        onDeleteSession={(deletedId) => {
          if (deletedId === sessionId) clear();
        }}
      />

      {/* ── Main area ── */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* ── Header ── */}
        <header className="flex items-center justify-between px-4 py-3 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/70 dark:border-slate-700/70 shadow-sm shrink-0 relative">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-slate-400 dark:via-slate-600 to-transparent" />

          <div className="flex items-center gap-3">
            {/* Sidebar toggle */}
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            {/* Logo + title */}
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-slate-600 flex items-center justify-center shadow-sm">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h16a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
                </svg>
              </div>
              <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Agentic AI Platform</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">

            {/* Export button */}
            {messages.length > 0 && !isLoading && (
              <button
                onClick={exportConversation}
                title="Export conversation"
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full font-medium border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export
              </button>
            )}

            {/* Dark mode toggle */}
            <button
              onClick={toggleDark}
              title={dark ? "Switch to light mode" : "Switch to dark mode"}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              {dark ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>

            {/* Backend status */}
            <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full font-medium border ${
              backendStatus === "online"   ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800"
              : backendStatus === "offline" ? "bg-red-50 text-red-600 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800"
              : "bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800"
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                backendStatus === "online"   ? "bg-emerald-500"
                : backendStatus === "offline" ? "bg-red-500"
                : "bg-amber-400 animate-pulse"
              }`} />
              {backendStatus === "online"   && "Connected"}
              {backendStatus === "offline"  && "Disconnected"}
              {backendStatus === "checking" && "Connecting"}
            </div>

          </div>
        </header>

        {/* ── Offline warning ── */}
        {backendStatus === "offline" && (
          <div className="mx-4 mt-3 px-4 py-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-xs rounded-xl flex items-start gap-2 shrink-0">
            <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>
              Cannot reach the backend. Start the server:
              <code className="ml-1.5 bg-red-100 dark:bg-red-900 px-1.5 py-0.5 rounded font-mono">
                uvicorn api.main:app --reload --port 8000
              </code>
            </span>
          </div>
        )}

        {/* ── Error banner ── */}
        {error && (
          <div className="mx-4 mt-3 px-4 py-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-xs rounded-xl flex items-center gap-2 shrink-0">
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {/* ── Chat card ── */}
        <div className="flex-1 overflow-hidden flex flex-col mx-4 my-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
          <ChatWindow messages={messages} onRegenerate={send} onEditSend={resendFromMessage} onTogglePin={togglePin} />
          <InputBar onSend={send} onStop={stop} isLoading={isLoading} />
        </div>

      </div>
    </div>
  );
}
