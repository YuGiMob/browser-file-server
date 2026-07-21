.PHONY: test run check clean

test:
	python -m unittest discover tests/

check:
	python -m server --check-config

run:
	python -m server

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
