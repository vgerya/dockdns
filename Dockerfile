FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Install Poetry
ENV POETRY_VERSION=1.8.2
RUN pip install "poetry==$POETRY_VERSION" --no-cache-dir

# Set working directory
ENV PYTHONPATH=app
WORKDIR /app

# Copy only required files first (for caching)
COPY pyproject.toml poetry.lock README.md ./
# Copy the actual source code
COPY app/ ./app


# Disable virtualenv creation in Docker
RUN poetry config virtualenvs.create false

# Install only main dependencies
RUN poetry install --only main

# Expose the default FastAPI port
EXPOSE 8080

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
