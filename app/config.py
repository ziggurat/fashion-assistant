import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Settings:
    DEFAULT_LLM_PROVIDER: str = "anthropic"
    DEFAULT_MODEL: str = "claude-3-7-sonnet-20250219"
    TEMPERATURE: float = 0.7
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
