# Dockerfile for Banking Data Pipeline (Spark/Python 3.9)
FROM python:3.9-slim-buster

# Install OpenJDK-11 (Required for Spark)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Environment variables for Spark
ENV SPARK_HOME=/usr/local/lib/python3.9/site-packages/pyspark
ENV PYTHONPATH=$PYTHONPATH:/app/src

# Default command
CMD ["python", "main.py"]
