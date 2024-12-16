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
COPY requirements.txt .

RUN pip install --upgrade pip wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

EXPOSE 8532
ENTRYPOINT ["python", "web-tool.py"]
