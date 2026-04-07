FROM python:3.13-slim

# Install system deps + clean apt cache in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv from official image (avoids extra pip layer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy all source + manifests before deps install (setuptools requires all package dirs present)
COPY pyproject.toml uv.lock ./
COPY library/ ./library/
COPY static/ ./static/
COPY templates/ ./templates/
COPY web-tool.py README.md ./

# Install deps
RUN uv pip install --system --no-cache .

# Non-root user for security (create before nltk download so data goes to their home)
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /data && chown appuser:appuser /data

# Download NLTK data to a world-readable location
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d /usr/share/nltk_data wordnet words

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8532/')" || exit 1

EXPOSE 8532
ENTRYPOINT ["python", "web-tool.py"]
