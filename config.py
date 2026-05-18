import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    api_secret_key: str = field(default_factory=lambda: os.getenv("API_SECRET_KEY", ""))
    model: str = "gpt-5-nano"
    max_completion_tokens: int = 16000
    max_search_results: int = 5
    max_agentic_iterations: int = 5


config = Config()
