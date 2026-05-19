import json
import logging
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from api.middleware.auth import verify_api_key
from api.models.requests import ChatRequest, ChatResponse, HealthResponse
from api.services.history import history_manager
from orchestrator import Orchestrator
from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[HistoryMessage]
    total_messages: int


logger = logging.getLogger("api")
router = APIRouter()

# Single orchestrator instance shared across all requests
orchestrator = Orchestrator()


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Public endpoint — no API key required.
    Used to check if the server is running.
    """
    return HealthResponse(status="ok", version="1.0")


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest):
    """
    Main conversational endpoint.

    Steps:
    1. Create or load the session
    2. Load previous conversation history
    3. Pass message + history to the orchestrator
    4. Save the user message and AI reply to history
    5. Return the reply and session_id
    """
    start = time.time()

    try:
        # Step 1: Create or load session
        session_id = history_manager.create_session(request.session_id)

        msg_preview = request.message[:100] + ("..." if len(request.message) > 100 else "")
        logger.info("=" * 60)
        logger.info(f"[CHAT] New request | session: {session_id[:8]} | message: '{msg_preview}'")
        logger.info(f"[CHAT] Message length: {len(request.message)} chars")

        # Step 2: Load previous conversation history as (role, content) tuples
        history = history_manager.get_messages_as_tuples(session_id)
        if history:
            logger.info(
                f"[CHAT] Loaded {len(history)} prior message(s) for session: {session_id[:8]}"
            )
        else:
            logger.info(f"[CHAT] No prior history — fresh conversation")

        # Step 3: Run the orchestrator with proper message history
        reply = orchestrator.run(request.message, session_id=session_id, history=history)

        # Step 5: Save both turns to history
        history_manager.add_message(session_id, "user", request.message)
        history_manager.add_message(session_id, "assistant", reply)

        elapsed_ms = int((time.time() - start) * 1000)
        reply_preview = reply[:100] + ("..." if len(reply) > 100 else "")
        logger.info(
            f"[CHAT] Request complete | session: {session_id[:8]} | "
            f"duration: {elapsed_ms}ms | reply: {len(reply)} chars"
        )
        logger.info(f"[CHAT] Reply preview: '{reply_preview}'")
        logger.info("=" * 60)

        return ChatResponse(reply=reply, session_id=session_id)

    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        logger.error(
            f"[CHAT] ERROR after {elapsed_ms}ms: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )


@router.post("/chat/stream", dependencies=[Depends(verify_api_key)])
async def chat_stream(request: ChatRequest):
    """Streaming version of /chat — sends tokens via Server-Sent Events."""
    session_id = history_manager.create_session(request.session_id)
    history = history_manager.get_messages_as_tuples(session_id)
    history_manager.add_message(session_id, "user", request.message)

    collected: list[str] = []

    async def generate():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        try:
            async for token in orchestrator.stream(request.message, session_id, history):
                collected.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as e:
            logger.error(f"[CHAT/STREAM] Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Always save history — runs even on exception or client disconnect
            full_response = "".join(collected)
            if full_response:
                history_manager.add_message(session_id, "assistant", full_response)
                logger.info(f"[CHAT/STREAM] Saved to history | session: {session_id[:8]} | {len(full_response)} chars")
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions", dependencies=[Depends(verify_api_key)])
async def list_sessions():
    """Return a list of all sessions with their title and message count."""
    return {"sessions": history_manager.get_all_sessions()}


@router.get("/history/{session_id}", response_model=HistoryResponse, dependencies=[Depends(verify_api_key)])
async def get_history(session_id: str):
    """
    Returns the full conversation history for a given session.

    How to use:
    1. Call POST /chat and note the session_id in the response
    2. Call GET /history/{session_id} to see the full conversation
    """
    messages = history_manager.get_messages(session_id)

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No history found for session_id: {session_id}"
        )

    return HistoryResponse(
        session_id=session_id,
        messages=[
            HistoryMessage(role=m.role, content=m.content)
            for m in messages
        ],
        total_messages=len(messages)
    )


class RenameRequest(BaseModel):
    title: str


@router.patch("/sessions/{session_id}/rename", dependencies=[Depends(verify_api_key)])
async def rename_session(session_id: str, body: RenameRequest):
    """Rename a session with a custom title."""
    if not history_manager.get_messages(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No session found for session_id: {session_id}"
        )
    if not body.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title cannot be empty."
        )
    history_manager.rename_session(session_id, body.title)
    logger.info(f"[CHAT] Session renamed | session: {session_id[:8]} | title: '{body.title}'")
    return {"message": "Session renamed successfully", "title": body.title.strip()}


@router.delete("/history/{session_id}", dependencies=[Depends(verify_api_key)])
async def clear_history(session_id: str):
    """
    Clears the conversation history for a given session.
    Use this to start a fresh conversation while keeping the same session_id.
    """
    messages = history_manager.get_messages(session_id)

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No history found for session_id: {session_id}"
        )

    history_manager.clear_session(session_id)
    logger.info(f"[CHAT] History cleared for session: {session_id}")
    return {"message": f"History cleared for session: {session_id}"}
