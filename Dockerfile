FROM python:3.12-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Configure global Playwright browser cache location (critical for non-root users)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install basic system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install poetry
RUN pip install --no-cache-dir --upgrade pip poetry

# Copy dependency configuration files first to utilize Docker build layer caching
COPY pyproject.toml poetry.lock* ./

# Configure poetry to install system-wide inside container & install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

# Install Playwright and Chromium browser binaries globally along with required system libraries
RUN playwright install --with-deps chromium

# Create a non-root user with UID 1000 (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user

# Copy the rest of the application files
COPY . .

# Create target directories for SQLite data and adjust ownership for both app files and playwright browsers
RUN mkdir -p /app/reports/data \
    && chown -R user:user /app \
    && chown -R user:user /ms-playwright

# Switch to the non-root user
USER user

# Set environment variables for Hugging Face Spaces (inbound port must be 7860)
ENV HOST=0.0.0.0
ENV PORT=7860
ENV HOME=/home/user

# Expose port 7860
EXPOSE 7860

# Start FastAPI server via unified run_server entrypoint
CMD ["python", "run_server.py"]
