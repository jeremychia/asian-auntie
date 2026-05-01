FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen

# Copy app code
COPY . .

# Expose port
EXPOSE 8080

# Run migrations and start app
CMD ["sh", "-c", "uv run flask --app wsgi db upgrade && uv run gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 wsgi:app"]
