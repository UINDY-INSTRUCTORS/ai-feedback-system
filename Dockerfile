# Dockerfile for AI Feedback System
# Used by GitHub Actions to run feedback generation scripts

FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir pyyaml requests

# Set working directory
WORKDIR /workspace

# Copy scripts
COPY scripts/ /workspace/scripts/

# Make scripts executable
RUN chmod +x /workspace/scripts/*.py

# Set Python to run in unbuffered mode (better for logs)
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["/bin/bash"]
