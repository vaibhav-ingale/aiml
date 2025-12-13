.PHONY: help up down restart logs build clean status ps scale-workers stop-service start-service

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║     Unified ML & Data Platform - Docker Manager           ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Compose Operations

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ All services started!$(NC)"
	@echo "$(CYAN)Access the dashboard at: http://local.lab$(NC)"

down: ## Stop and remove all containers
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ All services stopped!$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ All services restarted!$(NC)"

build: ## Build all images
	@echo "$(GREEN)Building all images...$(NC)"
	docker-compose build --no-cache
	@echo "$(GREEN)✓ All images built!$(NC)"

rebuild: down build up ## Rebuild and restart all services

##@ Service Management

start-postgres: ## Start PostgreSQL only
	docker-compose up -d postgres

start-pgadmin: ## Start pgAdmin only
	docker-compose up -d pgadmin

start-minio: ## Start MinIO only
	docker-compose up -d minio minio-setup

start-mlflow: ## Start MLflow only
	docker-compose up -d mlflow

start-spark: ## Start Spark cluster (master, workers, history)
	docker-compose up -d spark-master spark-worker spark-history-server

start-jupyter: ## Start Jupyter Lab only
	docker-compose up -d jupyter

start-nginx: ## Start Nginx only
	docker-compose up -d nginx

stop-postgres: ## Stop PostgreSQL
	docker-compose stop postgres

stop-pgadmin: ## Stop pgAdmin
	docker-compose stop pgadmin

stop-minio: ## Stop MinIO
	docker-compose stop minio

stop-mlflow: ## Stop MLflow
	docker-compose stop mlflow

stop-spark: ## Stop Spark cluster
	docker-compose stop spark-master spark-worker spark-history-server

stop-jupyter: ## Stop Jupyter Lab
	docker-compose stop jupyter

stop-nginx: ## Stop Nginx
	docker-compose stop nginx

restart-postgres: ## Restart PostgreSQL
	docker-compose restart postgres

restart-pgadmin: ## Restart pgAdmin
	docker-compose restart pgadmin

restart-minio: ## Restart MinIO
	docker-compose restart minio

restart-mlflow: ## Restart MLflow
	docker-compose restart mlflow

restart-spark: ## Restart Spark cluster
	docker-compose restart spark-master spark-worker spark-history-server

restart-jupyter: ## Restart Jupyter Lab
	docker-compose restart jupyter

restart-nginx: ## Restart Nginx
	docker-compose restart nginx

##@ Logs & Monitoring

logs: ## View logs for all services
	docker-compose logs -f

logs-postgres: ## View PostgreSQL logs
	docker-compose logs -f postgres

logs-pgadmin: ## View pgAdmin logs
	docker-compose logs -f pgadmin

logs-minio: ## View MinIO logs
	docker-compose logs -f minio

logs-mlflow: ## View MLflow logs
	docker-compose logs -f mlflow

logs-spark-master: ## View Spark Master logs
	docker-compose logs -f spark-master

logs-spark-worker: ## View Spark Worker logs
	docker-compose logs -f spark-worker

logs-spark-history: ## View Spark History Server logs
	docker-compose logs -f spark-history-server

logs-jupyter: ## View Jupyter Lab logs
	docker-compose logs -f jupyter

logs-nginx: ## View Nginx logs
	docker-compose logs -f nginx

##@ Scaling

scale-workers: ## Scale Spark workers (usage: make scale-workers WORKERS=3)
	@if [ -z "$(WORKERS)" ]; then \
		echo "$(RED)Error: WORKERS parameter required$(NC)"; \
		echo "$(YELLOW)Usage: make scale-workers WORKERS=3$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Scaling Spark workers to $(WORKERS)...$(NC)"
	docker-compose up -d --scale spark-worker=$(WORKERS)
	@echo "$(GREEN)✓ Spark workers scaled to $(WORKERS)!$(NC)"

##@ Status & Info

ps: ## List all running containers
	@docker-compose ps

status: ## Show detailed status of all services
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║              Service Status Overview                      ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

health: ## Check health status of all services
	@echo "$(CYAN)Checking health status...$(NC)"
	@docker ps --filter "name=postgres" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=pgadmin" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=minio" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=mlflow" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=spark-master" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=spark-worker" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=spark-history" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=jupyter" --format "{{.Names}}: {{.Status}}"
	@docker ps --filter "name=nginx" --format "{{.Names}}: {{.Status}}"

##@ Cleanup

clean: down ## Remove all containers, networks, and volumes
	@echo "$(RED)Removing all containers, networks, and volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

clean-volumes: ## Remove all volumes (WARNING: data will be lost!)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)✓ Volumes removed!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

prune: ## Remove all unused Docker resources
	@echo "$(YELLOW)Pruning unused Docker resources...$(NC)"
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Prune complete!$(NC)"

##@ URLs

urls: ## Display all service URLs
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║                   Service URLs                            ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Dashboard:$(NC)          http://local.lab"
	@echo ""
	@echo "$(GREEN)ML Tracking:$(NC)"
	@echo "  MLflow:             http://mlflow.lab"
	@echo "  pgAdmin:            http://pgadmin.lab"
	@echo ""
	@echo "$(GREEN)Data Processing:$(NC)"
	@echo "  Spark Master:       http://spark-master.lab"
	@echo "  Spark History:      http://spark-history.lab"
	@echo "  Spark Apps:         http://spark-app.lab"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  Jupyter Lab:        http://spark-jupyter.lab"
	@echo ""
	@echo "$(GREEN)Storage:$(NC)"
	@echo "  MinIO Console:      http://minio-console.lab"
	@echo "  MinIO API:          http://minio-api.lab"
	@echo ""
	@echo "$(YELLOW)Note: Add these domains to /etc/hosts pointing to 127.0.0.1$(NC)"

##@ Setup

setup-hosts: ## Display hosts file entries (macOS/Linux)
	@echo "$(CYAN)Add these lines to /etc/hosts:$(NC)"
	@echo ""
	@echo "127.0.0.1 local.lab"
	@echo "127.0.0.1 mlflow.lab"
	@echo "127.0.0.1 pgadmin.lab"
	@echo "127.0.0.1 minio-console.lab"
	@echo "127.0.0.1 minio-api.lab"
	@echo "127.0.0.1 spark-master.lab"
	@echo "127.0.0.1 spark-history.lab"
	@echo "127.0.0.1 spark-jupyter.lab"
	@echo "127.0.0.1 spark-app.lab"
	@echo ""
	@echo "$(YELLOW)On macOS/Linux, run:$(NC)"
	@echo "sudo make add-hosts"

add-hosts: ## Add entries to /etc/hosts (requires sudo)
	@echo "127.0.0.1 local.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 mlflow.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 pgadmin.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 minio-console.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 minio-api.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 spark-master.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 spark-history.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 spark-jupyter.lab" | sudo tee -a /etc/hosts
	@echo "127.0.0.1 spark-app.lab" | sudo tee -a /etc/hosts
	@echo "$(GREEN)✓ Hosts entries added!$(NC)"

##@ Development

shell-postgres: ## Open shell in PostgreSQL container
	docker-compose exec postgres psql -U postgres -d mlflow

shell-pgadmin: ## Open shell in pgAdmin container
	docker-compose exec pgadmin sh

shell-mlflow: ## Open shell in MLflow container
	docker-compose exec mlflow bash

shell-spark-master: ## Open shell in Spark Master container
	docker-compose exec spark-master bash

shell-jupyter: ## Open shell in Jupyter container
	docker-compose exec jupyter bash

shell-minio: ## Open shell in MinIO container
	docker-compose exec minio sh

shell-nginx: ## Open shell in Nginx container
	docker-compose exec nginx sh
