// ─── Chat ─────────────────────────────────────────────────────────────────────

// Matches ChatRequest in api/models/requests.py
export type ChatRequest = {
  message: string
  session_id?: string
}

// Matches ChatResponse in api/models/requests.py
export type ChatResponse = {
  reply: string
  session_id: string
}

// ─── Message & History ────────────────────────────────────────────────────────

// A single message in the conversation
// role "user" = sent by the human
// role "assistant" = sent by the AI
export type Message = {
  role: "user" | "assistant"
  content: string
}

// Matches HistoryResponse in api/routes/chat.py
export type HistoryResponse = {
  session_id: string
  messages: Message[]
  total_messages: number
}

// ─── Health ───────────────────────────────────────────────────────────────────

// Matches HealthResponse in api/models/requests.py
export type HealthResponse = {
  status: string
  version: string
}

// ─── UI State ─────────────────────────────────────────────────────────────────

// Extends Message with UI-only fields not stored in the backend
export type UIMessage = Message & {
  id: string                // unique ID for React key prop
  timestamp: Date           // when the message was sent
  skill?: SkillType         // which skill was invoked (AI messages only)
  isLoading?: boolean       // true while AI is still responding
  pinned?: boolean
  attachmentName?: string   // filename of attachment (user messages only)
}

// Which skill the agent decided to invoke
export type SkillType = "research" | "plan" | "both" | null

// ─── Sessions ────────────────────────────────────────────────────────────────

export type SessionInfo = {
  session_id: string
  title: string
  preview: string
  message_count: number
}

export type SessionsResponse = {
  sessions: SessionInfo[]
}

// ─── API Error ────────────────────────────────────────────────────────────────

// Shape of error responses from FastAPI
export type ApiError = {
  detail: string
}
