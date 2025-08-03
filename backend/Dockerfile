FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    libmagic1 \
    libmagic-dev \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (required for tokenizers)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set Java environment for Tika
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Copy requirements first for better caching
COPY requirements-minimal.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Download required NLTK data as root before switching users
RUN python -c "import nltk; nltk.download('punkt', download_dir='/usr/local/share/nltk_data'); nltk.download('stopwords', download_dir='/usr/local/share/nltk_data')"
ENV NLTK_DATA=/usr/local/share/nltk_data

# Copy application code
COPY app/ ./app/
COPY api/ ./api/
COPY tests/ ./tests/
COPY data/ ./data/

# Create required directories
RUN mkdir -p logs uploads cache

# Set Python path
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]