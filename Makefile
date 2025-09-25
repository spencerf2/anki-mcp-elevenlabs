.PHONY: help test fmt install-hooks

help:
	@echo "Available targets:"
	@echo "  fmt           - Format code with ruff"
	@echo "  install-hooks - Install git pre-commit hooks"
	@echo "  test          - Run all tests"
	@echo "  test FILE=... - Run specific test file"
	@echo "  help          - Show this help message"

fmt:
	poetry run ruff format .
	poetry run ruff check --fix .

install-hooks:
	./scripts/install-pre-commit-hook.sh

test:
	@if [ -n "$(FILE)" ]; then \
		echo "Running specific test file: $(FILE)"; \
		poetry run pytest anki_mcp_elevenlabs/tests/$(FILE) -v; \
	else \
		echo "Running all tests"; \
		poetry run pytest anki_mcp_elevenlabs/tests/ -v; \
	fi

