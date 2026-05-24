"use client";

import { useState, useCallback, useRef } from "react";
import { streamMessage, getHistory } from "@/lib/api";
import { UIMessage, SkillType } from "@/lib/types";

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

function detectSkill(reply: string): SkillType {
  const lower = reply.toLowerCase();
  const hasResearch =
    lower.includes("research") || lower.includes("source") ||
    lower.includes("found") || lower.includes("summary");
  const hasPlan =
    lower.includes("task") || lower.includes("plan") ||
    lower.includes("step") || lower.includes("phase");
  if (hasResearch && hasPlan) return "both";
  if (hasResearch) return "research";
  if (hasPlan) return "plan";
  return null;
}

export function useChat() {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isLoadingRef = useRef(false);

  // ── Send a message (optionally with a file attachment) ────────────────────
  const send = useCallback(async (text: string, file?: File | null) => {
    if (isLoadingRef.current) return;
    if (!text.trim() && !file) return;
    setError(null);

    // If a file is attached, read its content. The content is sent to the
    // backend silently as context — the user's chat bubble shows only their
    // text + a file chip with the filename.
    let fileContent = "";
    let fileName = "";
    if (file) {
      try {
        fileContent = await readFileAsText(file);
        fileName = file.name;
      } catch {
        setError("Could not read this file. Only text-based files are supported.");
        return;
      }
    }

    const userMessage: UIMessage = {
      id: generateId(),
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
      attachmentName: fileName || undefined,
    };
    setMessages((prev) => [...prev, userMessage]);

    const loadingId = generateId();
    setMessages((prev) => [...prev, {
      id: loadingId, role: "assistant", content: "", timestamp: new Date(), isLoading: true,
    }]);
    setIsLoading(true);

    isLoadingRef.current = true;
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let fullContent = "";

    // Combined payload for the LLM: user's text + file content (if any).
    // This is what the backend and the model see — not what the user sees.
    const backendMessage = fileContent
      ? `${text.trim() || "Please look at the attached file."}\n\n[Attached file: ${fileName}]\n\`\`\`\n${fileContent}\n\`\`\``
      : text.trim();

    try {
      const newSessionId = await streamMessage(
        backendMessage,
        sessionId,
        (token) => {
          fullContent += token;
          setMessages((prev) => prev.map((msg) =>
            msg.id === loadingId ? { ...msg, content: fullContent } : msg
          ));
        },
        controller.signal
      );
      setSessionId(newSessionId || sessionId);
      setMessages((prev) => prev.map((msg) =>
        msg.id === loadingId
          ? { ...msg, content: fullContent, isLoading: false, skill: detectSkill(fullContent) }
          : msg
      ));
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setMessages((prev) => prev.map((msg) =>
          msg.id === loadingId ? { ...msg, content: fullContent, isLoading: false } : msg
        ));
      } else {
        setMessages((prev) => prev.filter((msg) => msg.id !== loadingId));
        setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      }
    } finally {
      isLoadingRef.current = false;
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, [sessionId]);

  // ── Edit a message in-place and resend ───────────────────────────────────
  const resendFromMessage = useCallback(async (messageId: string, newContent: string) => {
    if (!newContent.trim() || isLoadingRef.current) return;
    setError(null);

    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === messageId);
      return idx === -1 ? prev : prev.slice(0, idx);
    });

    const userMessage: UIMessage = {
      id: generateId(), role: "user", content: newContent.trim(), timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const loadingId = generateId();
    setMessages((prev) => [...prev, {
      id: loadingId, role: "assistant", content: "", timestamp: new Date(), isLoading: true,
    }]);
    setIsLoading(true);
    isLoadingRef.current = true;

    const controller = new AbortController();
    abortControllerRef.current = controller;
    let fullContent = "";

    try {
      const newSessionId = await streamMessage(
        newContent.trim(),
        sessionId,
        (token) => {
          fullContent += token;
          setMessages((prev) => prev.map((msg) =>
            msg.id === loadingId ? { ...msg, content: fullContent } : msg
          ));
        },
        controller.signal
      );
      setSessionId(newSessionId || sessionId);
      setMessages((prev) => prev.map((msg) =>
        msg.id === loadingId
          ? { ...msg, content: fullContent, isLoading: false, skill: detectSkill(fullContent) }
          : msg
      ));
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setMessages((prev) => prev.map((msg) =>
          msg.id === loadingId ? { ...msg, content: fullContent, isLoading: false } : msg
        ));
      } else {
        setMessages((prev) => prev.filter((msg) => msg.id !== loadingId));
        setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      }
    } finally {
      isLoadingRef.current = false;
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, [sessionId]);

  // ── Stop the in-flight request ────────────────────────────────────────────
  const stop = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  // ── Load an existing session from history ─────────────────────────────────
  const loadSession = useCallback(async (targetSessionId: string) => {
    setError(null);
    try {
      const history = await getHistory(targetSessionId);
      const loaded: UIMessage[] = history.messages.map((m) => ({
        id: generateId(),
        role: m.role,
        content: m.content,
        timestamp: new Date(),
        isLoading: false,
      }));
      setMessages(loaded);
      setSessionId(targetSessionId);
    } catch {
      setError("Failed to load conversation.");
    }
  }, []);

  // ── Pin / unpin a message ─────────────────────────────────────────────────
  const togglePin = useCallback((messageId: string) => {
    setMessages((prev) => prev.map((m) =>
      m.id === messageId ? { ...m, pinned: !m.pinned } : m
    ));
  }, []);

  // ── Start a new conversation ──────────────────────────────────────────────
  const clear = useCallback(() => {
    setMessages([]);
    setSessionId(undefined);
    setError(null);
  }, []);

  return { messages, sessionId, isLoading, error, send, resendFromMessage, stop, togglePin, clear, loadSession };
}
