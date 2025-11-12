# Build stage: Install dependencies
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# Verify Flask installation
RUN pip show flask /
    pip -version

# Runtime stage: Use slim image for reliability
FROM python:3.9-slim
WORKDIR /app
# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --chown=nonroot:nonroot . .

# Create non-root user
RUN useradd -m nonroot
USER nonroot
EXPOSE 5000

# Health check
HEALTHCHECK CMD curl -f http://localhost:5000 || exit 1

CMD ["python3", "app.py"]
