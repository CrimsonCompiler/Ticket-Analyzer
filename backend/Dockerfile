# Backend image for Ticket Analyzer.
# - CPU-only torch keeps the image at ~600-800 MB (PRD requirement).
# - Model weights are baked into the image at build time via
#   from_pretrained(), and HF_HOME is set so the runtime container
#   finds the cache. TRANSFORMERS_OFFLINE=1 makes the container fail
#   loudly if weights are missing instead of silently downloading.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# CPU-only torch (much smaller than the default CUDA wheel).
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1

WORKDIR /app

COPY requirements.txt .
# Install the rest of the stack with the *default* PyPI index now that
# torch is already present.
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    'uvicorn[standard]==0.30.6' \
    sqlalchemy==2.0.36 \
    psycopg2-binary==2.9.10 \
    pydantic==2.9.2 \
    transformers==4.45.2

# Bake the tiny sentiment model into the image.
# NOTE: TRANSFORMERS_OFFLINE is intentionally NOT set here — the
# from_pretrained() call below needs network access to download the
# weights into the image's HF_HOME cache. TRANSFORMERS_OFFLINE=1 is
# set at runtime (via docker-compose env / docker run -e) so the
# container fails loudly if the cached weights are missing.
ENV HF_HOME=/opt/hf-cache
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    m='distilbert-base-uncased-finetuned-sst-2-english'; \
    AutoTokenizer.from_pretrained(m); \
    AutoModelForSequenceClassification.from_pretrained(m)"

COPY app ./app

EXPOSE 8000

# Set TRANSFORMERS_OFFLINE=1 only for the running uvicorn process so
# the dry-run acceptance criterion (no network to huggingface.co at
# runtime, weights must already be baked into the image) still holds.
ENV TRANSFORMERS_OFFLINE=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
