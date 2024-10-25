# Builder stage
FROM python:3.12-slim AS builder

# Install Poetry
RUN pip install poetry

# Copy project files
WORKDIR /app
COPY pyproject.toml ./
COPY main.py kubectl_handler.py ./
COPY llm_handlers ./llm_handlers/

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Runtime stage
FROM python:3.12-slim AS runtime

# Install kubectl
RUN apt-get update && apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/ && \
    apt-get remove -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the necessary files from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/main.py /app/kubectl_handler.py ./
COPY --from=builder /app/llm_handlers ./llm_handlers/

# Create directory for config
RUN mkdir -p /root/.kube

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV KUBECONFIG=/root/.kube/config

# Create entrypoint script
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
