PY = python
WEB = web

.PHONY: setup test dev api web-build lint typecheck check

setup:
	$(PY) -m pip install -e ".[dev]"
	cd $(WEB) && pnpm install

test:
	$(PY) -m pytest tests/ -q

lint:
	$(PY) -m ruff check src tests
	cd $(WEB) && pnpm lint

typecheck:
	$(PY) -m mypy src
	cd $(WEB) && pnpm typecheck

check: lint typecheck test
	cd $(WEB) && pnpm build

openapi-baseline:
	SECURITY_PASSPORT_PROVIDER=fixtures \
	SECURITY_PASSPORT_FIXTURES=tests/fixtures/corpus \
		$(PY) scripts/export_openapi.py > tests/fixtures/openapi-baseline.json

openapi-check:
	SECURITY_PASSPORT_PROVIDER=fixtures \
	SECURITY_PASSPORT_FIXTURES=tests/fixtures/corpus \
		$(PY) scripts/export_openapi.py > .openapi-current.json
	oasdiff breaking tests/fixtures/openapi-baseline.json \
		.openapi-current.json --fail-on ERR

dev-api:
	$(PY) -m uvicorn security_passport.api.app:app --reload --host 127.0.0.1 --port 8000

dev-web:
	cd $(WEB) && pnpm dev

update:
	$(PY) -m security_passport.cli.main update

validate:
	$(PY) -m security_passport.cli.main validate

doctor:
	$(PY) -m security_passport.cli.main doctor
