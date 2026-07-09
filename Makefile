.PHONY: install lint test test-backend test-ai test-web test-mobile security-check docker-up migrate migration-verify
install:
	python -m pip install -e melanintruth-ai/services/api[dev]
lint:
	python -m ruff check melanintruth-ai/services/api/app/backend melanintruth-ai/services/api/app/api/phase3_app.py melanintruth-ai/services/api/app/api/deps.py melanintruth-ai/services/api/app/api/router.py melanintruth-ai/services/api/app/api/routes melanintruth-ai/services/api/app/db melanintruth-ai/services/api/app/schemas melanintruth-ai/services/api/app/services/wiring.py melanintruth-ai/services/api/app/services/container.py melanintruth-ai/services/api/app/core/config.py melanintruth-ai/services/api/app/main.py melanintruth-ai/tests
	python -m compileall melanintruth-ai/services/api/app/backend melanintruth-ai/services/api/app/api/phase3_app.py melanintruth-ai/services/api/app/api/deps.py melanintruth-ai/services/api/app/api/router.py melanintruth-ai/services/api/app/api/routes melanintruth-ai/services/api/app/db melanintruth-ai/services/api/app/schemas melanintruth-ai/services/api/app/services melanintruth-ai/services/api/app/core/config.py melanintruth-ai/services/api/app/main.py -q

test: test-backend test-ai
test-backend:
	python -m pytest melanintruth-ai/tests/unit melanintruth-ai/tests/integration
test-ai:
	python -m pytest melanintruth-ai/tests/ai-evaluation
test-api:
	python -m pytest melanintruth-ai/tests/integration/test_phase3_api.py
migrate-test:
	PYTHONPATH=melanintruth-ai/services/api python -c "from app.db.session import connect_sqlite; conn=connect_sqlite(); assert conn.execute('select count(*) from records').fetchone()[0] == 0"
test-fastapi:
	python -m pytest melanintruth-ai/tests/api_fastapi melanintruth-ai/tests/integration/test_phase35_fastapi_contract.py
openapi-check:
	PYTHONPATH=melanintruth-ai/services/api python -c "from app.api.router import create_fastapi_app; app=create_fastapi_app(); spec=app.openapi() if hasattr(app, 'openapi') else app.openapi_contract(); assert '/analysis/jobs' in spec['paths']"
test-postgres:
	python -m pytest melanintruth-ai/tests/integration/test_phase35_fastapi_contract.py
test-web:
	cd melanintruth-ai/apps/web && npm test
test-mobile:
	cd melanintruth-ai/apps/mobile && flutter test
security-check:
	python -m pip_audit || true
	python -m bandit -q -r melanintruth-ai/services/api/app melanintruth-ai/ml || true
docker-up:
	docker compose up -d postgres redis
migrate:
	cd melanintruth-ai/services/api && alembic upgrade head

api-install:
	python -m pip install -r melanintruth-ai/services/api/requirements.txt
api-run:
	PYTHONPATH=melanintruth-ai/services/api uvicorn app.main:app --reload
api-test:
	PYTHONPATH=melanintruth-ai/services/api python -m pytest melanintruth-ai/tests/api_fastapi melanintruth-ai/tests/integration/test_phase35_fastapi_contract.py
api-openapi:
	PYTHONPATH=melanintruth-ai/services/api python -m app.tools.export_openapi docs/api/openapi.json
api-migrate:
	cd melanintruth-ai/services/api && PYTHONPATH=. alembic upgrade head
migration-verify:
	PYTHONPATH=melanintruth-ai/services/api python -m app.tools.verify_migration_tables
api-docker-build:
	docker compose -f docker-compose.api.yml build api
api-docker-test:
	docker compose -f docker-compose.api.yml run --rm api python -m pytest /app/melanintruth-ai/tests/api_fastapi /app/melanintruth-ai/tests/integration/test_phase36_sqlmodel_contract.py
postgres-up:
	docker compose -f docker-compose.api.yml up -d postgres
postgres-down:
	docker compose -f docker-compose.api.yml down
test-postgres-real:
	python -m pytest melanintruth-ai/tests/integration/test_phase36_sqlmodel_contract.py
