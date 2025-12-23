# Makefile for Banking Data Pipeline Framework

VENV = .venv
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip

.PHONY: setup test run clean docker-build help

help:
	@echo "Available commands:"
	@echo "  make setup   - Create virtual environment and install dependencies"
	@echo "  make test    - Run unit and integration tests with pytest"
	@echo "  make run     - Execute the main pipeline runner"
	@echo "  make clean   - Remove caches, temporary files, and the .venv"

setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/

run:
	$(PYTHON) main.py

clean:
	@if exist $(VENV) rmdir /s /q $(VENV)
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@del /s /q *.pyc logs/*.log data/raw/*.csv data/silver/*.parquet data/gold/*.parquet
