# Enterprise Dockerfile for Banking Data Pipeline (Bitnami Spark)
FROM bitnami/spark:3.5.0

# Set user to root to install dependencies
USER root

# Install Python dependencies and Arrow support
RUN apt-get update && apt-get install -y python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Environment setup
ENV PYTHONPATH=$PYTHONPATH:/app/src
ENV BANKING_ENCRYPTION_KEY="ENTERPRISE_DEMO_KEY_DO_NOT_USE_IN_PROD"

# Create necessary directories
RUN mkdir -p data/raw data/bronze data/silver data/gold data/quarantine logs

# Run the pipeline by default
ENTRYPOINT ["python3", "main.py"]
