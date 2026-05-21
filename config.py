import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    api_secret_key: str = field(default_factory=lambda: os.getenv("API_SECRET_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("MODEL", "gpt-4o-mini"))
    max_completion_tokens: int = 4000
    max_search_results: int = 2
    max_agentic_iterations: int = 3


config = Config()
