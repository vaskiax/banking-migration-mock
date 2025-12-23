# Enterprise Makefile for Banking Data Pipeline

IMAGE_NAME = banking-enterprise-pipeline
CONTAINER_NAME = banking-job-run

.PHONY: setup test run build run-container clean help

help:
	@echo "Enterprise Commands:"
	@echo "  make setup         - Local setup (venv + pip)"
	@echo "  make test          - Run tests locally"
	@echo "  make run           - Run pipeline locally"
	@echo "  make build         - Build Docker image (Instruction 4)"
	@echo "  make run-container - Run container with volumes (Instruction 4)"
	@echo "  make clean         - Deep clean of all artifacts"

setup:
	python -m venv .venv
	.venv/Scripts/pip install -r requirements.txt

test:
	.venv/Scripts/python -m pytest tests/

run:
	.venv/Scripts/python main.py

build:
	docker build -t $(IMAGE_NAME) .

run-container:
	docker run --rm --name $(CONTAINER_NAME) \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/logs:/app/logs" \
		$(IMAGE_NAME)

clean:
	@if exist .venv rmdir /s /q .venv
	@if exist data rmdir /s /q data
	@if exist logs rmdir /s /q logs
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@mkdir data\raw data\bronze data\silver data\gold data\quarantine logs
