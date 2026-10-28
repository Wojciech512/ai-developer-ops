# ai-developer-ops gates. /ai-developer-ops:init fills the TODO targets for this stack.
SHA256 := $(shell command -v shasum >/dev/null 2>&1 && echo "shasum -a 256" || echo sha256sum)

check: lint typecheck test docs-fresh
lint: ; @echo "TODO: lint"
typecheck: ; @echo "TODO: typecheck"
test: ; @echo "TODO: test"
fmt-file: ; @echo "TODO: format $(FILE)"
e2e: ; @echo "TODO: run app + playwright smoke"

# One shell statement on purpose: an `exit 0` on its own recipe line would
# end only that line's shell, and make would run the rest - writing a digest
# for an SVG that was never rendered.
docs:
	@if [ ! -f docs/architecture.puml ]; then \
		echo "docs: no docs/architecture.puml, nothing to render"; \
	elif command -v plantuml >/dev/null 2>&1; then \
		plantuml -tsvg docs/architecture.puml && \
		$(SHA256) docs/architecture.puml | cut -d' ' -f1 > docs/architecture.svg.sha256 && \
		echo "docs: rendered docs/architecture.svg"; \
	elif command -v docker >/dev/null 2>&1; then \
		docker run --rm -v "$$PWD/docs:/data" plantuml/plantuml -tsvg /data/architecture.puml && \
		$(SHA256) docs/architecture.puml | cut -d' ' -f1 > docs/architecture.svg.sha256 && \
		echo "docs: rendered docs/architecture.svg"; \
	else \
		echo "docs: neither plantuml nor docker found; docs/architecture.svg not refreshed"; \
	fi

# Binds the image to the source by content, not by mtime: git does not
# restore mtimes, so a stale committed SVG would pass an mtime check.
docs-fresh:
	@if [ ! -f docs/architecture.puml ]; then exit 0; fi; \
	 if [ ! -f docs/architecture.svg.sha256 ]; then \
		echo "docs/architecture.svg.sha256 is missing; run make docs"; exit 1; fi; \
	 have=$$($(SHA256) docs/architecture.puml | cut -d' ' -f1); \
	 want=$$(cat docs/architecture.svg.sha256); \
	 if [ "$$have" != "$$want" ]; then \
		echo "docs/architecture.svg is stale for docs/architecture.puml; run make docs"; \
		exit 1; fi

.PHONY: check lint typecheck test fmt-file e2e docs docs-fresh
