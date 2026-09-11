.PHONY: bootstrap up down test smoke logs backup
bootstrap:
	python3 scripts/bootstrap.py
up:
	docker compose up -d --build --wait
down:
	docker compose down
test:
	docker compose exec api pytest -q
smoke:
	curl --fail http://localhost:8082/api/health/
logs:
	docker compose logs --tail=100 api worker scheduler
backup:
	python3 scripts/backup.py
