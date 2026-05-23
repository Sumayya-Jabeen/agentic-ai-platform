from langchain_tavily import TavilySearch
from config import config


class WebSearchTool:
    """Provides LangChain's TavilySearch as the web search tool."""

    def __init__(self):
        self._tool = TavilySearch(
            max_results=config.max_search_results,
            tavily_api_key=config.tavily_api_key
        )

    def get_tool(self):
        """Return the LangChain tool for use in AgentExecutor."""
        return self._tool
