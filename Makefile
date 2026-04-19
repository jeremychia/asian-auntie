.PHONY: dev setup migrate

dev:
	uv run flask --app wsgi run --host=0.0.0.0 --port=8080 --debug

setup:
	uv sync
	cp -n .env.example .env || true
	uv run flask --app wsgi db upgrade

migrate:
	uv run flask --app wsgi db migrate -m "$(msg)"
	uv run flask --app wsgi db upgrade
