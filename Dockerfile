FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_ALLOW_NON_LOOPBACK=true \
    MCP_PORT=8000

RUN groupadd --system app && useradd --system --gid app --home-dir /app app
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
       CMD python -c "import os,socket; socket.create_connection(('127.0.0.1', int(os.environ['MCP_PORT'])), timeout=3).close()" || exit 1

CMD ["aquamatrix-simar-mcp"]