.PHONY: install dev build clean test lint

install:
	pip install .

dev:
	pip install -e .

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info honeychow/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint:
	ruff check honeychow/

format:
	ruff format honeychow/

publish:
	python -m twine upload dist/*

publish-test:
	python -m twine upload --repository testpypi dist/*
