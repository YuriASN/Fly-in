EXCLUDES = --exclude '.venv/'

install:
	uv sync

run:
	uv run pyhton3 main.py

debug:

clean:
	@find . -type d \( -name '.mypy_cache' -o -name '__pycache__' \) \
	-print -exec rm -rf {} +

lint:
	-uv run flake8 $(EXCLUDES) .
	-uv run mypy --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs \
	$(EXCLUDES) *.py

lint-strict:
	-uv run flake8 $(EXCLUDES) .
	-uv run mypy --strict $(EXCLUDES) *.py