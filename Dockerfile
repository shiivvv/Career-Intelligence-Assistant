FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (requires separate setup on host or modify this approach)
# Note: Ollama is typically run on the host machine and accessed via network
# For production, consider using ollama container separately and linking networks

WORKDIR /app

# Copy project files
COPY requirements.txt .
COPY rag.py .
COPY app.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for data
RUN mkdir -p chroma_db sample_jobs

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
