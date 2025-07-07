FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

# Install dependencies
RUN uv sync --frozen --no-dev

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create home directory and cache directory for appuser
RUN mkdir -p /home/appuser/.cache/uv && \
    chown -R appuser:appuser /home/appuser

# Set ownership of app directory
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/servers || exit 1

# Run the application
CMD ["uv", "run", "ssh-remote-control", "web", "--host", "0.0.0.0", "--port", "8000"]
