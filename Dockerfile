FROM python:3.11-slim

# Cairo is required for SVG conversion.
RUN apt-get update && \
    apt-get install -y build-essential libcairo2-dev

WORKDIR /app

COPY web-tool.py .
COPY README.md .
COPY library/ ./library/
COPY static/ ./static/
COPY templates/ ./templates/
COPY pyproject.toml .
COPY uv.lock .

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies using uv
RUN uv pip install --system .

# Install NLTK data.
RUN python -m nltk.downloader wordnet words

EXPOSE 8532
ENTRYPOINT ["python", "web-tool.py"]
