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
		plantuml -tsvg docs/architecture.puml && $(MAKE) -s docs-stamp; \
	elif command -v docker >/dev/null 2>&1; then \
		docker run --rm -v "$$PWD/docs:/data" plantuml/plantuml -tsvg /data/architecture.puml && \
		$(MAKE) -s docs-stamp; \
	else \
		echo "docs: neither plantuml nor docker found; docs/architecture.svg not refreshed"; \
	fi

# Records the digest of the source the SVG was rendered from. The digest is
# captured into a variable first: `$(SHA256) f | cut ...` takes its status
# from cut, so a missing or failing hash tool would silently store an empty
# digest that docs-fresh would then accept.
docs-stamp:
	@digest=$$($(SHA256) docs/architecture.puml) || { \
		echo "docs: $(SHA256) failed on docs/architecture.puml"; exit 1; }; \
	 digest=$$(printf '%s' "$$digest" | cut -d' ' -f1); \
	 if [ -z "$$digest" ]; then \
		echo "docs: empty digest from $(SHA256); refusing to stamp"; exit 1; fi; \
	 printf '%s\n' "$$digest" > docs/architecture.svg.sha256; \
	 echo "docs: rendered docs/architecture.svg"

# Binds the image to the source by content, not by mtime: git does not
# restore mtimes, so a stale committed SVG would pass an mtime check.
docs-fresh:
	@if [ ! -f docs/architecture.puml ]; then exit 0; fi; \
	 if [ ! -f docs/architecture.svg ]; then \
		echo "docs/architecture.svg is missing; run make docs"; exit 1; fi; \
	 if [ ! -f docs/architecture.svg.sha256 ]; then \
		echo "docs/architecture.svg.sha256 is missing; run make docs"; exit 1; fi; \
	 have=$$($(SHA256) docs/architecture.puml) || { \
		echo "docs-fresh: $(SHA256) failed on docs/architecture.puml"; exit 1; }; \
	 have=$$(printf '%s' "$$have" | cut -d' ' -f1); \
	 want=$$(cat docs/architecture.svg.sha256); \
	 if [ -z "$$have" ] || [ -z "$$want" ]; then \
		echo "docs-fresh: empty digest; run make docs"; exit 1; fi; \
	 if [ "$$have" != "$$want" ]; then \
		echo "docs/architecture.svg is stale for docs/architecture.puml; run make docs"; \
		exit 1; fi

.PHONY: check lint typecheck test fmt-file e2e docs docs-stamp docs-fresh
