import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from models import ResearchInput, ResearchOutput
from tools.web_search import WebSearchTool
from callbacks import PipelineLogger
from config import config


logger = logging.getLogger("api")

SYSTEM_PROMPT = """You are a research assistant. Your job is to research a given topic
by searching the web and gathering information from multiple sources.

Follow these steps:
1. Start with a broad search to understand the topic
2. Follow up with more specific searches based on what you find
3. Search 3 to 5 times total to gather enough information
4. After all searches, write a clear and comprehensive summary

Be focused and stop searching once you have enough information to answer the query well."""


class ResearchSkill:
    """
    Research & Summarization Skill.

    How it works:
    - Phase 1 (Gather): AgentExecutor runs the web search loop automatically.
                        The model decides what to search and when to stop.
    - Phase 2 (Synthesize): with_structured_output() converts the gathered
                            context into a clean ResearchOutput Pydantic model.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.model,
            api_key=config.openai_api_key,
            max_completion_tokens=config.max_completion_tokens
        )
        self.web_search = WebSearchTool()

    def run(self, input: ResearchInput) -> ResearchOutput:
        """Main entry point. Takes a ResearchInput and returns a ResearchOutput."""
        logger.info(f"  [RESEARCH] Starting research for query: '{input.query}'")
        if input.focus_areas:
            logger.info(f"  [RESEARCH] Focus areas: {input.focus_areas}")

        try:
            # Phase 1: AgentExecutor handles the search loop
            context = self._gather_information(input)

            # Phase 2: Convert gathered context into structured output
            return self._synthesize(input, context)

        except Exception as e:
            logger.error(
                f"  [RESEARCH] ERROR during research for '{input.query}': "
                f"{type(e).__name__}: {e}"
            )
            raise

    # ─── Phase 1: Information Gathering ──────────────────────────────────────

    def _gather_information(self, input: ResearchInput) -> str:
        """
        AgentExecutor runs the model + web_search loop until the model
        decides it has enough information. Replaces the manual for-loop.
        """
        logger.info(
            f"  [RESEARCH] Phase 1 START — web search agent "
            f"(max_iterations: {config.max_agentic_iterations})"
        )

        cb = PipelineLogger("RESEARCH-SEARCH")
        tools = [self.web_search.get_tool()]

        focus = (
            f"\nFocus on these areas: {', '.join(input.focus_areas)}"
            if input.focus_areas else ""
        )

        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT
        )

        result = agent.invoke(
            {"messages": [("human", f"Research this topic thoroughly: {input.query}{focus}")]},
            config={"callbacks": [cb]}
        )

        context = result["messages"][-1].content
        logger.info(
            f"  [RESEARCH] Phase 1 COMPLETE | {cb.summary()} | "
            f"gathered context: {len(context)} chars"
        )
        return context

    # ─── Phase 2: Synthesis ───────────────────────────────────────────────────

    def _synthesize(self, input: ResearchInput, context: str) -> ResearchOutput:
        """
        with_structured_output() replaces client.beta.chat.completions.parse().
        LangChain handles the schema enforcement automatically.
        """
        logger.info(
            f"  [RESEARCH] Phase 2 START — synthesizing {len(context)} chars "
            f"into structured ResearchOutput"
        )

        cb = PipelineLogger("RESEARCH-SYNTH")
        structured_llm = self.llm.with_structured_output(ResearchOutput)

        output: ResearchOutput = structured_llm.invoke(
            [
                (
                    "system",
                    "You are a research synthesizer. Given raw research context, "
                    "produce a clean structured research output. "
                    "Assign credibility scores: 0.9 for academic or official sources, "
                    "0.7 for reputable news or blogs, 0.5 for unknown sources."
                ),
                (
                    "human",
                    f"Synthesize this research into a structured output.\n"
                    f"Original query: {input.query}\n\n"
                    f"Gathered context:\n{context}"
                )
            ],
            config={"callbacks": [cb]}
        )

        logger.info(
            f"  [RESEARCH] Phase 2 COMPLETE | "
            f"summary: {len(output.summary)} chars | "
            f"key_points: {len(output.key_points)} | "
            f"sources: {len(output.sources)} | "
            f"confidence: {output.confidence:.2f} | "
            f"{cb.summary()}"
        )
        return output
