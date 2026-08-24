# Dockerfile for Hugging Face Spaces
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Hugging Face Spaces require a non-root user for security
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code and assign ownership to 'user'
COPY --chown=user . $HOME/app

# Switch to the non-root user
USER user

# Hugging Face explicitly maps web traffic to port 7860
EXPOSE 7860

# Make the start script executable
RUN chmod +x start.sh

# Run both the MCP Server and Streamlit using our custom script
CMD ["./start.sh"]
