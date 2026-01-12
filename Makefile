.PHONY: help setup start stop restart logs clean backup restore test

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)NBS Archive System - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Initial setup - copy .env and create directories
	@echo "$(GREEN)Setting up NBS Archive System...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file. Please review and update values.$(NC)"; \
	fi
	@mkdir -p logs/odoo logs/nginx nginx/ssl
	@echo "$(GREEN)Created log directories$(NC)"
	@echo "$(GREEN)Setup complete! Run 'make start' to begin.$(NC)"

start: ## Start all services
	@echo "$(GREEN)Starting NBS Archive System...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend API: http://localhost:8069"
	@echo "Odoo Admin: http://localhost:8069/web"

stop: ## Stop all services
	@echo "$(YELLOW)Stopping NBS Archive System...$(NC)"
	docker-compose stop

restart: ## Restart all services
	@echo "$(YELLOW)Restarting NBS Archive System...$(NC)"
	docker-compose restart

down: ## Stop and remove all containers
	@echo "$(RED)Stopping and removing all containers...$(NC)"
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-odoo: ## Show Odoo logs
	docker-compose logs -f odoo

logs-frontend: ## Show Frontend logs
	docker-compose logs -f frontend

logs-nginx: ## Show Nginx logs
	docker-compose logs -f nginx

ps: ## Show running containers
	docker-compose ps

shell-odoo: ## Open shell in Odoo container
	docker-compose exec odoo /bin/bash

shell-frontend: ## Open shell in Frontend container
	docker-compose exec frontend /bin/sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U odoo_user -d odoo_new

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

clean: ## Clean up volumes and containers (WARNING: deletes data!)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf logs/odoo/* logs/nginx/*; \
		echo "$(GREEN)Cleanup complete$(NC)"; \
	fi

backup: ## Create backup of database and files
	@echo "$(GREEN)Creating backup...$(NC)"
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U odoo_user odoo_new | gzip > backups/db_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)Database backup created$(NC)"

restore: ## Restore from backup (Usage: make restore FILE=backups/db_YYYYMMDD_HHMMSS.sql.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify backup file$(NC)"; \
		echo "Usage: make restore FILE=backups/db_YYYYMMDD_HHMMSS.sql.gz"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring from $(FILE)...$(NC)"
	@gunzip -c $(FILE) | docker-compose exec -T postgres psql -U odoo_user -d odoo_new
	@echo "$(GREEN)Restore complete$(NC)"

install-module: ## Install NBS Archive module in Odoo
	@echo "$(GREEN)Installing NBS Archive module...$(NC)"
	docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_new -i nbs_archive --stop-after-init
	@echo "$(GREEN)Module installed! Restart Odoo: make restart$(NC)"

update-module: ## Update NBS Archive module
	@echo "$(YELLOW)Updating NBS Archive module...$(NC)"
	docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_new -u nbs_archive --stop-after-init
	@echo "$(GREEN)Module updated! Restart Odoo: make restart$(NC)"

test-backend: ## Run backend tests
	@echo "$(GREEN)Running backend tests...$(NC)"
	docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_new --test-enable --stop-after-init

test-frontend: ## Run frontend tests
	@echo "$(GREEN)Running frontend tests...$(NC)"
	docker-compose exec frontend npm test

build: ## Build all services
	@echo "$(GREEN)Building all services...$(NC)"
	docker-compose build

pull: ## Pull latest images
	@echo "$(GREEN)Pulling latest images...$(NC)"
	docker-compose pull

init-db: ## Initialize Odoo database
	@echo "$(GREEN)Initializing Odoo database...$(NC)"
	docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_new --init=base --stop-after-init
	@echo "$(GREEN)Database initialized!$(NC)"

opensearch-status: ## Check OpenSearch status
	@curl -s http://localhost:9200/_cluster/health?pretty

create-admin: ## Create admin user (interactive)
	@echo "$(GREEN)Creating admin user...$(NC)"
	docker-compose exec odoo python3 -c "import xmlrpc.client; url='http://localhost:8069'; db='odoo_new'; username='admin'; password='Admin123!'; common=xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url)); uid=common.authenticate(db, username, password, {}); print('Admin user created/verified. UID:', uid)"

dev: ## Start in development mode with live reload
	@echo "$(GREEN)Starting in development mode...$(NC)"
	docker-compose -f docker-compose.yml up

prod: ## Start in production mode
	@echo "$(GREEN)Starting in production mode...$(NC)"
	@echo "$(YELLOW)Make sure to configure SSL in nginx.conf$(NC)"
	docker-compose up -d

status: ## Show system status
	@echo "$(GREEN)=== NBS Archive System Status ===$(NC)"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(YELLOW)Database Connection:$(NC)"
	@docker-compose exec -T postgres pg_isready -U odoo_user && echo "$(GREEN)✓ PostgreSQL OK$(NC)" || echo "$(RED)✗ PostgreSQL Down$(NC)"
	@echo ""
	@echo "$(YELLOW)OpenSearch:$(NC)"
	@curl -s http://localhost:9200/_cluster/health | grep -q "green\|yellow" && echo "$(GREEN)✓ OpenSearch OK$(NC)" || echo "$(RED)✗ OpenSearch Down$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose exec -T redis redis-cli ping | grep -q "PONG" && echo "$(GREEN)✓ Redis OK$(NC)" || echo "$(RED)✗ Redis Down$(NC)"

urls: ## Show application URLs
	@echo "$(GREEN)=== Application URLs ===$(NC)"
	@echo "Frontend:        http://localhost:5173"
	@echo "Backend API:     http://localhost:8069/api"
	@echo "Odoo Web:        http://localhost:8069/web"
	@echo "OpenSearch:      http://localhost:9200"
	@echo "PostgreSQL:      localhost:5432"


















