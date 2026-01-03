# DefenderAgent Makefile

.PHONY: help build up down logs shell test clean install

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)DefenderAgent - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install Python dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	pip install -r requirements.txt

build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker-compose build

up: ## Start the DefenderAgent container
	@echo "$(GREEN)Starting DefenderAgent...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Container started!$(NC)"

down: ## Stop the DefenderAgent container
	@echo "$(YELLOW)Stopping DefenderAgent...$(NC)"
	docker-compose down

restart: down up ## Restart the container

logs: ## View container logs
	docker-compose logs -f agent

shell: ## Open shell in the container
	docker-compose exec agent /bin/bash

run-task: ## Run a coding task (requires TASK, REPO, BRANCH variables)
	@if [ -z "$(TASK)" ] || [ -z "$(REPO)" ] || [ -z "$(BRANCH)" ]; then \
		echo "$(YELLOW)Usage: make run-task TASK='description' REPO='url' BRANCH='branch-name'$(NC)"; \
		exit 1; \
	fi
	python run_task.py --repo "$(REPO)" --task "$(TASK)" --branch "$(BRANCH)"

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	@echo "$(GREEN)Running linters...$(NC)"
	black --check src/
	pylint src/
	mypy src/

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	black src/

clean: ## Clean up generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/

clean-all: clean down ## Clean everything including Docker resources
	@echo "$(YELLOW)Removing Docker volumes...$(NC)"
	docker-compose down -v
	docker system prune -f

setup: install build ## Initial setup (install deps + build image)
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Copy .env.example to .env and configure"
	@echo "  2. Run 'make up' to start the container"
	@echo "  3. Run 'make run-task' to execute a coding task"

status: ## Show container status
	@echo "$(GREEN)Container Status:$(NC)"
	docker-compose ps

version: ## Show version
	@echo "DefenderAgent v0.1.0"
