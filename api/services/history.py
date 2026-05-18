import uuid
from typing import List, Optional
from dataclasses import dataclass, field


MAX_HISTORY_TURNS = 10  # Keep last 10 conversation turns per session


@dataclass
class Message:
    """A single message in a conversation turn."""
    role: str   # "user" or "assistant"
    content: str


@dataclass
class Session:
    """All messages belonging to one conversation session."""
    session_id: str
    messages: List[Message] = field(default_factory=list)


class ConversationHistory:
    """
    In-memory conversation history manager.

    Think of it as a notebook with one page per user session.
    Each page holds the last 10 exchanges so the AI remembers context.

    How it works:
    - Each user gets a unique session_id (auto-generated if not provided)
    - Every message they send + every AI reply gets saved to that session
    - When /chat is called again with the same session_id, history is
      loaded and passed to the orchestrator as context
    - Old sessions never expire in this implementation (in-memory only)
    """

    def __init__(self):
        # Dict of session_id → Session
        self._sessions: dict[str, Session] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new session or return an existing one.
        If session_id is not provided, a new UUID is generated.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)

        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to a session.
        Automatically trims to MAX_HISTORY_TURNS to avoid unbounded growth.
        """
        if session_id not in self._sessions:
            self.create_session(session_id)

        session = self._sessions[session_id]
        session.messages.append(Message(role=role, content=content))

        # Keep only the last N turns (each turn = 1 user + 1 assistant message)
        max_messages = MAX_HISTORY_TURNS * 2
        if len(session.messages) > max_messages:
            session.messages = session.messages[-max_messages:]

    def get_history_as_context(self, session_id: str) -> str:
        """
        Return the conversation history as a plain text string.
        This is passed to the orchestrator so the AI has context
        from previous turns.

        Example output:
            User: Research AI agents
            Assistant: Here is what I found...
            User: Now make a plan
        """
        if session_id not in self._sessions:
            return ""

        messages = self._sessions[session_id].messages
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{role_label}: {msg.content}")

        return "\n".join(lines)

    def get_all_sessions(self) -> list:
        """Return summary metadata for every session that has at least one message."""
        result = []
        for session_id, session in self._sessions.items():
            user_messages = [m for m in session.messages if m.role == "user"]
            if not user_messages:
                continue
            first = user_messages[0].content
            result.append({
                "session_id": session_id,
                "title": first[:60] + ("..." if len(first) > 60 else ""),
                "preview": first[:100] + ("..." if len(first) > 100 else ""),
                "message_count": len(session.messages),
            })
        return result

    def get_messages_as_tuples(self, session_id: str) -> list:
        """
        Return messages as (role, content) tuples ready for LangChain.
        LangChain expects "human" / "assistant" role names.
        """
        if session_id not in self._sessions:
            return []
        return [
            ("human" if msg.role == "user" else "assistant", msg.content)
            for msg in self._sessions[session_id].messages
        ]

    def get_messages(self, session_id: str) -> List[Message]:
        """Return raw list of Message objects for a session."""
        if session_id not in self._sessions:
            return []
        return self._sessions[session_id].messages

    def clear_session(self, session_id: str):
        """Delete all messages for a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Single shared instance used across all routes
history_manager = ConversationHistory()
