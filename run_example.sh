#!/usr/bin/env bash
# run_example.sh — set up and run the django-multiseek example projects.
#
# Subcommands:
#   setup [name]   migrate + fetch_assets + initial_data for one or all
#   run   <name>   setup + start the dev server (foreground)
#   test  [name]   setup + run the example's Playwright test suite
#
# Without arguments, prints help.
#
# Example projects live under examples/. Each ships a `fetch_assets`
# management command that downloads its JS/CSS dependencies into
# static/multiseek/vendor/ — that's why `setup` runs before `run`/`test`.

set -euo pipefail

EXAMPLES=(minimal bootstrap alpine htmx)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
    cat <<EOF
Usage:
  $(basename "$0") setup [example]     prep one example (or all if omitted)
  $(basename "$0") run   <example>     prep then start runserver on :8000
  $(basename "$0") test  [example]     prep then run pytest (one example, or all)

Available examples: ${EXAMPLES[*]}

Each example uses its own SQLite DB and its own static/multiseek/vendor/
download cache. Re-running setup is idempotent — fetch_assets skips
files already present, migrate is no-op when up to date, initial_data
uses get_or_create.
EOF
}

# Resolve the example argument to a directory. Fails if the name isn't
# in the canonical EXAMPLES list.
resolve_example() {
    local name="$1"
    for ex in "${EXAMPLES[@]}"; do
        if [[ "$ex" == "$name" ]]; then
            printf '%s/examples/%s\n' "$SCRIPT_DIR" "$name"
            return 0
        fi
    done
    echo "ERROR: '$name' is not a known example." >&2
    echo "Choose one of: ${EXAMPLES[*]}" >&2
    return 1
}

setup_one() {
    local name="$1"
    local dir
    dir="$(resolve_example "$name")"
    echo "=== $name :: setup ==="
    (
        cd "$dir"
        # alpine has its own pyproject.toml + .venv; the others use the
        # repo-root venv via uv's upward-pyproject lookup.
        if [[ -f pyproject.toml ]]; then
            uv sync --all-extras
        fi
        uv run python manage.py migrate --noinput
        uv run python manage.py fetch_assets
        uv run python manage.py initial_data
    )
    echo ""
}

setup_all() {
    for ex in "${EXAMPLES[@]}"; do
        setup_one "$ex"
    done
}

run_one() {
    local name="$1"
    local dir
    dir="$(resolve_example "$name")"
    setup_one "$name"
    echo "=== $name :: serving at http://127.0.0.1:8000/multiseek/ ==="
    cd "$dir"
    exec uv run python manage.py runserver
}

test_one() {
    local name="$1"
    local dir
    dir="$(resolve_example "$name")"
    setup_one "$name"
    echo "=== $name :: pytest (chromium) ==="
    cd "$dir"
    uv run pytest --browser chromium
}

test_all() {
    local failed=()
    for ex in "${EXAMPLES[@]}"; do
        if ! test_one "$ex"; then
            failed+=("$ex")
        fi
    done
    if (( ${#failed[@]} > 0 )); then
        echo ""
        echo "FAILED: ${failed[*]}" >&2
        return 1
    fi
    echo ""
    echo "All ${#EXAMPLES[@]} examples passed."
}

main() {
    case "${1:-}" in
        ""|-h|--help|help)
            usage
            ;;
        setup)
            if [[ -n "${2:-}" ]]; then setup_one "$2"; else setup_all; fi
            ;;
        run)
            if [[ -z "${2:-}" ]]; then
                echo "ERROR: 'run' requires an example name." >&2
                usage
                exit 1
            fi
            run_one "$2"
            ;;
        test)
            if [[ -n "${2:-}" ]]; then test_one "$2"; else test_all; fi
            ;;
        *)
            echo "ERROR: unknown subcommand '$1'." >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"
