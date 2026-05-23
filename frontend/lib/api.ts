import {
  ChatRequest,
  ChatResponse,
  HistoryResponse,
  HealthResponse,
  SessionsResponse,
} from "./types";

// ─── Config ───────────────────────────────────────────────────────────────────

function getApiUrl(): string {
  if (typeof window === "undefined") return "http://localhost:8000";
  return `http://${window.location.hostname}:8000`;
}

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

// ─── Base fetch helper ────────────────────────────────────────────────────────

// Every request goes through this function.
// It automatically adds the X-API-Key header and handles errors.
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

// ─── API Functions ────────────────────────────────────────────────────────────

/**
 * Send a message to the AI agent.
 * The agent decides internally whether to invoke Research, Task Planner, or both.
 *
 * @param message   - The user's message
 * @param sessionId - Optional. Pass the session_id from a previous response
 *                    to continue an existing conversation.
 */
export async function sendMessage(
  message: string,
  sessionId?: string,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const body: ChatRequest = { message, session_id: sessionId };
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

/**
 * Fetch the full conversation history for a session.
 *
 * @param sessionId - The session ID returned by sendMessage
 */
export async function getHistory(sessionId: string): Promise<HistoryResponse> {
  return apiFetch<HistoryResponse>(`/history/${sessionId}`);
}

/**
 * Clear the conversation history for a session.
 * Use this when the user wants to start a fresh conversation.
 *
 * @param sessionId - The session ID to clear
 */
export async function clearHistory(sessionId: string): Promise<void> {
  await apiFetch<{ message: string }>(`/history/${sessionId}`, {
    method: "DELETE",
  });
}

/**
 * Check if the backend is alive and reachable.
 * Returns { status: "ok", version: "1.0" } if healthy.
 */
export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function getSessions(): Promise<SessionsResponse> {
  return apiFetch<SessionsResponse>("/sessions");
}

export async function renameSession(sessionId: string, title: string): Promise<void> {
  await apiFetch<{ message: string; title: string }>(`/sessions/${sessionId}/rename`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

/**
 * Stream a message token-by-token via Server-Sent Events.
 * Calls onToken for each token as it arrives.
 * Returns the session_id once streaming is complete.
 */
export async function streamMessage(
  message: string,
  sessionId: string | undefined,
  onToken: (token: string) => void,
  signal?: AbortSignal
): Promise<string> {
  const response = await fetch(`${getApiUrl()}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let newSessionId = sessionId ?? "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      const event = JSON.parse(raw);
      if (event.type === "session") newSessionId = event.session_id;
      else if (event.type === "token") onToken(event.content);
      else if (event.type === "error") throw new Error(event.message);
    }
  }

  return newSessionId;
}
