import json
import logging
import time
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from skills.research import ResearchSkill
from skills.task_planner import TaskPlannerSkill
from models import ResearchInput, TaskPlanInput, ExecutionMode
from callbacks import PipelineLogger
from config import config

logger = logging.getLogger("api")


SYSTEM_PROMPT = """You are an intelligent assistant with access to two powerful skills:

1. research_topic  — searches the web and returns a structured summary with key points and sources
2. create_task_plan — breaks a goal into an ordered, actionable task plan

Rules — follow these strictly:
- ANY question asking about a topic, technology, comparison, or "what is / which is / how does" → call research_topic
- ANY request for a plan, steps, roadmap, or "how to do X" → call create_task_plan
- If the user asks to research AND plan → call research_topic first, then pass its summary into create_task_plan
- Only skip the skills for simple greetings or clarification questions (e.g. "hello", "thank you")
- After all skill calls are done, write a clear, helpful final response to the user
- Always end your final response with a single, short follow-up question on a new line that naturally continues the conversation. The question must be directly relevant to what was just discussed. Examples based on context:
  - After researching a topic: "Would you like me to create an action plan based on this research?"
  - After creating a plan: "Shall I break down any of these steps in more detail?"
  - After explaining a concept: "Would you like me to research the latest developments on this?"
  - After a general answer: "Is there a specific aspect you'd like me to explore further?"

Always be concise and practical in your final response.
- Format all responses using Markdown: use **bold** for key terms, *italic* for emphasis, `code` for technical terms, headers (##, ###) to separate sections, and bullet or numbered lists for any multi-item content."""


class Orchestrator:
    """
    The Orchestrator is the brain of the agentic system.

    AgentExecutor replaces the manual tool-call loop — it automatically routes
    tool calls, feeds results back, and stops when the model finishes.
    Both skills are exposed as @tool-decorated functions so LangChain can
    invoke them just like any other tool.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.model,
            api_key=config.openai_api_key,
            max_completion_tokens=config.max_completion_tokens
        )
        self.research_skill = ResearchSkill()
        self.task_planner = TaskPlannerSkill(research_skill=self.research_skill)

    async def stream(self, user_goal: str, session_id: str = "", history: list = None):
        """Stream final response tokens, skipping internal tool-call JSON."""
        from langchain_openai import ChatOpenAI as _ChatOpenAI
        streaming_llm = _ChatOpenAI(
            model=config.model,
            api_key=config.openai_api_key,
            max_completion_tokens=config.max_completion_tokens,
            streaming=True,
        )
        tools = self._build_tools()
        agent = create_agent(model=streaming_llm, tools=tools, system_prompt=SYSTEM_PROMPT)
        messages_input = list(history) if history else []
        messages_input.append(("human", user_goal))

        async for event in agent.astream_events({"messages": messages_input}, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if (isinstance(chunk.content, str)
                        and chunk.content
                        and not getattr(chunk, "tool_call_chunks", None)):
                    yield chunk.content

    def run(self, user_goal: str, session_id: str = "", history: list = None) -> str:
        """
        Main entry point.

        Takes the user's goal and optional conversation history as (role, content) tuples.
        Passing history as proper message objects lets the agent understand follow-up
        questions in context instead of treating every message as a new conversation.
        """
        session_label = f"session={session_id[:8]}" if session_id else "no-session"
        goal_preview = user_goal[:120] + ("..." if len(user_goal) > 120 else "")

        logger.info("=" * 60)
        logger.info(f"[ORCHESTRATOR] START | {session_label}")
        logger.info(f"[ORCHESTRATOR] User goal: '{goal_preview}'")
        if history:
            logger.info(f"[ORCHESTRATOR] Conversation history: {len(history)} prior message(s)")
        else:
            logger.info(f"[ORCHESTRATOR] No prior history — fresh conversation")
        logger.info(f"[ORCHESTRATOR] Tools available: research_topic, create_task_plan")

        tools = self._build_tools()
        cb = PipelineLogger("ORCHESTRATOR")

        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT
        )

        # Build message thread: all prior turns + the new user message
        messages = list(history) if history else []
        messages.append(("human", user_goal))

        start = time.time()
        try:
            result = agent.invoke(
                {"messages": messages},
                config={"callbacks": [cb]}
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error(
                f"[ORCHESTRATOR] ERROR after {elapsed_ms}ms: "
                f"{type(e).__name__}: {e}"
            )
            raise

        reply = result["messages"][-1].content
        elapsed_ms = int((time.time() - start) * 1000)

        if cb.iteration == 0:
            logger.info("[ORCHESTRATOR] AGENT DECISION --> No skill invoked (answered from own knowledge)")
        else:
            logger.info(f"[ORCHESTRATOR] AGENT DECISION --> {cb.iteration} skill(s) invoked")

        logger.info(
            f"[ORCHESTRATOR] COMPLETE | {cb.summary()} | "
            f"total messages in thread: {len(result['messages'])} | "
            f"reply length: {len(reply)} chars"
        )
        return reply

    # ─── Skill Tools ──────────────────────────────────────────────────────────

    def _build_tools(self) -> list:
        """
        Wrap both skills as LangChain @tool functions.
        The docstring becomes the tool description the model reads.
        The type hints become the input schema.
        """
        research_skill = self.research_skill
        task_planner = self.task_planner

        @tool
        def research_topic(query: str) -> str:
            """Search the web and return a structured summary with key points, sources, and confidence score. Call this when the user needs information gathered before making a plan."""
            logger.info("----------------------------------------------------------")
            logger.info("  AGENT DECISION --> RESEARCH SKILL selected")
            logger.info(f"  Input query : '{query}'")
            logger.info("----------------------------------------------------------")

            try:
                output = research_skill.run(ResearchInput(query=query))
            except Exception as e:
                logger.error(f"  RESEARCH SKILL FAILED: {type(e).__name__}: {e}")
                raise

            result = json.dumps({
                "summary": output.summary,
                "key_points": output.key_points,
                "gaps": output.gaps,
                "confidence": output.confidence,
                "sources": [
                    {"title": s.title, "url": s.url}
                    for s in output.sources
                ]
            })
            logger.info("----------------------------------------------------------")
            logger.info("  RESEARCH SKILL done")
            logger.info(f"  Summary    : {len(output.summary)} chars")
            logger.info(f"  Key points : {len(output.key_points)}")
            logger.info(f"  Sources    : {len(output.sources)}")
            logger.info(f"  Confidence : {output.confidence:.2f}")
            logger.info("----------------------------------------------------------")
            return result

        @tool
        def create_task_plan(goal: str, context: str = "") -> str:
            """Break a goal into an ordered, actionable task plan with dependencies and estimated durations. Pass research context if available to get a better informed plan."""
            logger.info("----------------------------------------------------------")
            logger.info("  AGENT DECISION --> TASK PLANNING SKILL selected")
            logger.info(f"  Goal       : '{goal}'")
            if context:
                logger.info(f"  Context    : {len(context)} chars (from Research Skill)")

            try:
                output = task_planner.run(TaskPlanInput(
                    goal=goal,
                    context=context if context else None,
                    execution_mode=ExecutionMode.PLAN_ONLY
                ))
            except Exception as e:
                logger.error(f"  TASK PLANNING SKILL FAILED: {type(e).__name__}: {e}")
                raise

            result = json.dumps({
                "plan": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "depends_on": t.depends_on,
                        "estimated_duration": t.estimated_duration
                    }
                    for t in output.plan
                ],
                "next_action": output.next_action,
                "blockers": output.blockers
            })
            logger.info("----------------------------------------------------------")
            logger.info("  TASK PLANNING SKILL done")
            logger.info(f"  Tasks generated : {len(output.plan)}")
            logger.info(f"  Next action     : '{output.next_action}'")
            logger.info("----------------------------------------------------------")
            return result

        return [research_topic, create_task_plan]
