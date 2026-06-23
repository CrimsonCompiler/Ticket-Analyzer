import os
from pathlib import Path

# All values are required. The application refuses to start if any
# environment variable is missing — this is intentional so a misconfigured
# deployment fails loudly instead of silently falling back to a default.
def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Check the .env file (or docker-compose env_file)."
        )
    return value


DATABASE_URL: str = _required("DATABASE_URL")
MODEL_NAME: str = _required("MODEL_NAME")
HF_HOME: str = _required("HF_HOME")
TRANSFORMERS_OFFLINE: str = _required("TRANSFORMERS_OFFLINE")

# Confidence threshold below which the raw POSITIVE/NEGATIVE label is
# downgraded to UNCERTAIN. Must be parseable as float.
SENTIMENT_CONFIDENCE_THRESHOLD: float = float(
    os.getenv("SENTIMENT_CONFIDENCE_THRESHOLD", "0.80")
)

# Ensure the cache directory exists at startup so the model loader finds it
Path(HF_HOME).mkdir(parents=True, exist_ok=True)
