"use client";

import { useState, useRef, KeyboardEvent } from "react";

type Props = {
  onSend: (message: string, file?: File | null) => void;
  onStop?: () => void;
  isLoading: boolean;
};

const MAX_FILE_SIZE = 100 * 1024; // 100 KB

export default function InputBar({ onSend, onStop, isLoading }: Props) {
  const [text, setText] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (isLoading) return;
    if (!text.trim() && !attachedFile) return;

    onSend(text.trim(), attachedFile);
    setText("");
    setAttachedFile(null);
    setFileError("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    e.target.value = "";

    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      setFileError(`File too large. Maximum size is ${MAX_FILE_SIZE / 1024} KB.`);
      setAttachedFile(null);
      return;
    }

    setFileError("");
    setAttachedFile(file);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-700 px-4 py-4 shrink-0 rounded-b-2xl">
      <div className="max-w-3xl mx-auto">

        {/* File error */}
        {fileError && (
          <div className="mb-2 px-3 py-1.5 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-xs rounded-lg">
            {fileError}
          </div>
        )}

        {/* File chip */}
        {attachedFile && (
          <div className="flex items-center gap-1.5 mb-2 px-1">
            <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 text-xs px-2.5 py-1 rounded-full">
              <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              <span className="max-w-[200px] truncate">{attachedFile.name}</span>
              <button
                onClick={() => setAttachedFile(null)}
                className="ml-0.5 text-slate-400 hover:text-slate-600 transition-colors"
                title="Remove attachment"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        <div className="flex items-end gap-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-2xl px-3 py-2 shadow-sm focus-within:border-slate-400 dark:focus-within:border-slate-500 focus-within:ring-2 focus-within:ring-slate-100 dark:focus-within:ring-slate-700 transition-all">

          {/* Hidden file input */}
          <input ref={fileInputRef} type="file" onChange={handleFileChange} className="hidden" />

          {/* Attachment button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Attach file"
            disabled={isLoading}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors shrink-0 mb-0.5 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>

          {/* Divider */}
          <div className="w-px h-5 bg-slate-200 dark:bg-slate-600 shrink-0 mb-0.5" />

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none bg-transparent text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none disabled:opacity-60 max-h-36 overflow-y-auto py-1"
            style={{ minHeight: "28px" }}
          />

          {/* Stop / Send button */}
          {isLoading ? (
            <button
              onClick={onStop}
              title="Stop generating"
              className="p-2 bg-red-500 text-white rounded-xl hover:bg-red-600 active:scale-95 transition-all shrink-0 mb-0.5 shadow-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="1" />
              </svg>
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!text.trim() && !attachedFile}
              className="p-2 bg-slate-600 text-white rounded-xl hover:bg-slate-700 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 mb-0.5 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          )}

        </div>

      </div>
    </div>
  );
}
