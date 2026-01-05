.PHONY: up down logs build restart clean test upload-templates

up:
	docker-compose up -d --build

down:
	docker-compose down

logs:
	docker-compose logs -f nda-backend

build:
	docker-compose build

restart:
	docker-compose restart nda-backend

clean:
	docker-compose down -v

test:
	docker-compose exec nda-backend python scripts/test_api.py

upload-templates:
	docker-compose exec nda-backend python scripts/upload_templates.py

ps:
	docker-compose ps
