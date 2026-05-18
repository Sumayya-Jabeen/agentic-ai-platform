"use client";

import { useEffect, useRef } from "react";
import { UIMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";

type Props = {
  messages: UIMessage[];
  onRegenerate: (content: string) => void;
  onEditSend: (messageId: string, newContent: string) => void;
  onTogglePin: (messageId: string) => void;
};

export default function ChatWindow({ messages, onRegenerate, onEditSend, onTogglePin }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const pinned = messages.filter((m) => m.pinned);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const scrollToMessage = (id: string) => {
    document.getElementById(`msg-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  return (
    <div className="flex-1 overflow-y-auto chat-scroll bg-white dark:bg-slate-900 flex flex-col">

      {/* ── Pinned bar ── */}
      {pinned.length > 0 && (
        <div className="shrink-0 border-b border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950 px-4 py-2 space-y-1.5">
          {pinned.map((m) => (
            <div key={m.id} className="flex items-start gap-2">
              <svg className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M16 12V4h1a1 1 0 000-2H7a1 1 0 000 2h1v8l-2 2v2h5v5l1 1 1-1v-5h5v-2l-2-2z" />
              </svg>
              <button
                onClick={() => scrollToMessage(m.id)}
                className="flex-1 text-xs text-amber-800 dark:text-amber-300 text-left truncate hover:underline"
              >
                {m.content.slice(0, 120)}{m.content.length > 120 ? "…" : ""}
              </button>
              <button
                onClick={() => onTogglePin(m.id)}
                title="Unpin"
                className="shrink-0 text-amber-400 hover:text-amber-600 dark:hover:text-amber-200 transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Messages ── */}
      <div className="flex-1 px-4 py-6">
        <div className="max-w-3xl mx-auto">

          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-slate-600 flex items-center justify-center shadow-md">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">How can I help you today?</h2>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((message) => (
              <div id={`msg-${message.id}`} key={message.id}>
                <MessageBubble
                  message={message}
                  onRegenerate={onRegenerate}
                  onEditSend={onEditSend}
                  onTogglePin={onTogglePin}
                />
              </div>
            ))}
          </div>

          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
