# Entrada unica a las tareas del proyecto. Lo que esta aca es lo mismo
# que ejecutan el CI y los agentes: si un comando solo funciona a mano,
# en un rato no funciona.
#
# Varios objetivos todavia no corren porque backend/ y frontend/ estan
# por armarse. El contrato esta definido y los andamios lo cumplen.

.PHONY: help install up migrate seed test lint typecheck openapi-generate openapi-check front-lint

help:
	@echo "install            instala dependencias de backend y frontend"
	@echo "up                 levanta Postgres y la API en local"
	@echo "migrate            aplica las migraciones pendientes"
	@echo "seed               carga datos de ejemplo (nunca datos reales)"
	@echo "test               tests del backend"
	@echo "lint               ruff check + ruff format --check"
	@echo "typecheck          mypy sobre app/"
	@echo "openapi-generate   regenera docs/api/openapi.json"
	@echo "openapi-check      falla si el contrato no esta al dia"

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm ci

up:
	docker compose up -d db
	cd backend && uvicorn app.main:app --reload

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python ../scripts/seed.py

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check . && ruff format --check .

typecheck:
	cd backend && mypy app

openapi-generate:
	cd backend && python -c "import json, pathlib; from app.main import app; \
pathlib.Path('../docs/api/openapi.json').write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')"

openapi-check: openapi-generate
	git diff --exit-code -- docs/api/openapi.json

front-lint:
	cd frontend && npm run lint && npm run build
