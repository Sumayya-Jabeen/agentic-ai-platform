import logging
import time
from typing import Any, Dict, List, Union
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger("api")


class PipelineLogger(BaseCallbackHandler):
    """
    LangChain callback handler that logs every agent step.

    Attach via:  agent.invoke(input, config={"callbacks": [PipelineLogger("LABEL")]})
    Read summary after invoke: cb.summary()
    """

    def __init__(self, context: str):
        super().__init__()
        self.context = context
        self.iteration = 0       # counts tool calls
        self.llm_call_count = 0  # counts LLM round-trips
        self.start_time = time.time()

    # ─── LLM Events ──────────────────────────────────────────────────────────
    # ChatOpenAI fires on_chat_model_start (not on_llm_start), so we handle both.

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        self._log_llm_start(serialized)

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        **kwargs: Any,
    ) -> None:
        self._log_llm_start(serialized)

    def _log_llm_start(self, serialized: Dict[str, Any]) -> None:
        self.llm_call_count += 1
        model = (
            serialized.get("kwargs", {}).get("model_name")
            or serialized.get("kwargs", {}).get("model")
            or "unknown"
        )
        logger.info(f"  [{self.context}] LLM call #{self.llm_call_count} (model: {model})")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        usage = {}
        if response.llm_output:
            usage = response.llm_output.get("token_usage", {})
        if usage:
            logger.info(
                f"  [{self.context}] LLM done | "
                f"prompt_tokens: {usage.get('prompt_tokens', '?')} | "
                f"completion_tokens: {usage.get('completion_tokens', '?')}"
            )

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        logger.error(f"  [{self.context}] LLM ERROR: {type(error).__name__}: {error}")

    # ─── Tool Events ─────────────────────────────────────────────────────────

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        self.iteration += 1
        tool_name = serialized.get("name", "unknown_tool")
        preview = str(input_str)[:200] + ("..." if len(str(input_str)) > 200 else "")
        logger.info(
            f"  [{self.context}] --- Iteration {self.iteration}: "
            f"Tool '{tool_name}' called ---"
        )
        logger.info(f"  [{self.context}] Input: {preview}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        preview = str(output)[:300] + ("..." if len(str(output)) > 300 else "")
        logger.info(f"  [{self.context}] Tool result (preview): {preview}")

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        logger.error(
            f"  [{self.context}] TOOL ERROR: {type(error).__name__}: {error}"
        )

    # ─── Chain / Agent Events ─────────────────────────────────────────────────

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        logger.error(
            f"  [{self.context}] CHAIN ERROR: {type(error).__name__}: {error}"
        )

    # ─── Summary ─────────────────────────────────────────────────────────────

    def summary(self) -> str:
        elapsed = time.time() - self.start_time
        return (
            f"tool_calls={self.iteration} | "
            f"llm_calls={self.llm_call_count} | "
            f"elapsed={elapsed:.2f}s"
        )
