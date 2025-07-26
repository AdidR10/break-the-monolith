# CUET Rickshaw Makefile

.PHONY: help build dev prod stop clean logs shell test

help: ## Show this help message
	@echo "CUET Rickshaw Docker Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up

prod: ## Start production environment
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

clean: ## Stop and remove all containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

logs: ## View logs from all services
	docker-compose logs -f

shell: ## Open shell in the app container
	docker-compose exec cuet-rickshaw-app sh

test: ## Run tests
	docker-compose exec cuet-rickshaw-app npm test

restart: ## Restart all services
	docker-compose restart

status: ## Show status of all services
	docker-compose ps

backup: ## Backup database
	docker-compose exec postgres pg_dump -U cuet_user cuet_rickshaw > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restore database (usage: make restore FILE=backup.sql)
	docker-compose exec -T postgres psql -U cuet_user cuet_rickshaw < $(FILE)
