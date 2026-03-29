from dotenv import load_dotenv
load_dotenv()

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    google_api_key: str
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    audit_log_path: str = "./audit_log.jsonl"
    enable_error_injection: bool = False
    llm_routing_enabled: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


# Constants
GROQ_MODEL: str = "llama-3.3-70b-versatile"
GEMINI_MODEL: str = "gemini-2.0-flash"
MAX_RETRIES: int = 3
RETRY_DELAY_SECONDS: float = 2.0

# Module-level singleton
settings = Settings()
