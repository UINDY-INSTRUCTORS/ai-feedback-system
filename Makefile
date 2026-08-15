CANONICAL := ../quarto-courses/shared/check_qmd.py
LOCAL     := scripts/check_qmd.py

.PHONY: sync-check-qmd test

sync-check-qmd:
	@if [ ! -f "$(CANONICAL)" ]; then \
		echo "ERROR: canonical copy not found at $(CANONICAL)"; exit 1; \
	fi
	cp $(CANONICAL) $(LOCAL)
	@echo "Synced check_qmd.py from quarto-courses/shared/"

test:
	uv run pytest tests/
