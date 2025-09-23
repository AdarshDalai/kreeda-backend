# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security first
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Copy Python dependencies from builder stage to appuser's local directory
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini .
COPY docker-entrypoint.sh .

# Change ownership of everything to appuser
RUN chown -R appuser:appuser /app /home/appuser/.local

# Add appuser's local python packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use exec form for proper signal handling
CMD ["./docker-entrypoint.sh"]
