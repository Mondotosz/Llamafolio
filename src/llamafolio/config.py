import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str
    groq_api_key: str
    groq_model: str
    tavily_api_key: str
    langsmith_api_key: str | None
    langsmith_project: str


def load_settings() -> Settings:
    return Settings(
        alpaca_api_key=_required("ALPACA_API_KEY"),
        alpaca_secret_key=_required("ALPACA_SECRET_KEY"),
        alpaca_base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        groq_api_key=_required("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        tavily_api_key=_required("TAVILY_API_KEY"),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "llamafolio"),
    )
