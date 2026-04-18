# === Builder stage: compile dependencies ===
FROM python:3.14-slim AS builder

# Install build deps + clean apt cache in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first (cache-friendly: code changes don't invalidate pip layer)
COPY pyproject.toml uv.lock ./

# Copy source code (setuptools requires all package dirs present)
COPY library/ ./library/
COPY routes/ ./routes/
COPY static/ ./static/
COPY templates/ ./templates/
COPY web-tool.py README.md ./

# Install Python dependencies
RUN uv pip install --system --no-cache .

# Download NLTK data to a world-readable location
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d /usr/share/nltk_data wordnet words

# === Runtime stage: minimal production image ===
FROM python:3.14-slim

# Install only runtime system deps (no compiler, no dev headers)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libcairo2 wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/

# Copy NLTK data from builder
COPY --from=builder /usr/share/nltk_data /usr/share/nltk_data
ENV NLTK_DATA=/usr/share/nltk_data

WORKDIR /app

# Copy application source (changes most frequently — last layer)
COPY library/ ./library/
COPY routes/ ./routes/
COPY static/ ./static/
COPY templates/ ./templates/
COPY web-tool.py README.md ./

# Non-root user for security
RUN useradd --uid 1000 --create-home appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /data && chown appuser:appuser /data

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8532/ || exit 1

EXPOSE 8532
ENTRYPOINT ["python", "web-tool.py"]