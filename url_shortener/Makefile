test:
	uv run pytest -n auto

run:
	uv run --project . python -m src.url_shortener

ci:
	uv run ruff --check --fix
	uv run mypy .