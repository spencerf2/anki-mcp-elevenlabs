.PHONY: help test

test:
	@if [ -n "$(FILE)" ]; then \
		echo "Running specific test file: $(FILE)"; \
		poetry run pytest anki_mcp_elevenlabs/tests/$(FILE) -v; \
	else \
		echo "Running all tests"; \
		poetry run pytest anki_mcp_elevenlabs/tests/ -v; \
	fi

help:
	@echo "Available targets:"
	@echo "  test          - Run all tests"
	@echo "  test FILE=... - Run specific test file"
	@echo "  help          - Show this help message"
