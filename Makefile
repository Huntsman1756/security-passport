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
