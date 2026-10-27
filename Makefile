# ai-developer-ops gates. Stack: bash scripts + markdown/JSON/TOML templates.
PY := $(shell [ -x .venv/bin/python3 ] && echo .venv/bin/python3 || command -v python3)
SH := $(shell git ls-files '*.sh') .githooks/pre-push templates/pre-push

check: lint typecheck test

lint:
	shellcheck $(SH)

typecheck:
	@for f in $(SH); do bash -n "$$f" || exit 1; done
	@for f in $$(git ls-files '*.json'); do jq empty "$$f" || { echo "invalid JSON: $$f"; exit 1; }; done
	@for f in $$(git ls-files '*.toml'); do $(PY) -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" "$$f" || { echo "invalid TOML: $$f"; exit 1; }; done
	@echo "typecheck OK"

test:
	$(PY) -m unittest discover -s tests -t .

fmt-file:
	@case "$(FILE)" in *.sh) command -v shfmt >/dev/null && shfmt -w "$(FILE)" || true ;; esac

e2e:
	bash tests/e2e_smoke.sh

.PHONY: check lint typecheck test fmt-file e2e
