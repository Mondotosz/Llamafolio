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
    # Alpaca
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str
    # LLM provider selection
    llm_provider: str  # "groq" or "gemini"
    # Groq (optional when llm_provider != "groq")
    groq_api_key: str | None
    groq_model: str
    # Gemini (optional when llm_provider != "gemini")
    google_api_key: str | None
    gemini_model: str
    # External tools
    tavily_api_key: str
    # LangSmith
    langsmith_api_key: str | None
    langsmith_project: str


def load_settings() -> Settings:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider not in {"groq", "gemini"}:
        raise RuntimeError(
            f"LLM_PROVIDER must be 'groq' or 'gemini', got {provider!r}"
        )

    # Only require the credentials for the active provider.
    groq_key = (
        _required("GROQ_API_KEY") if provider == "groq" else os.getenv("GROQ_API_KEY")
    )
    google_key = (
        _required("GOOGLE_API_KEY")
        if provider == "gemini"
        else os.getenv("GOOGLE_API_KEY")
    )

    return Settings(
        alpaca_api_key=_required("ALPACA_API_KEY"),
        alpaca_secret_key=_required("ALPACA_SECRET_KEY"),
        alpaca_base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        llm_provider=provider,
        groq_api_key=groq_key,
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        google_api_key=google_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        tavily_api_key=_required("TAVILY_API_KEY"),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "llamafolio"),
    )
