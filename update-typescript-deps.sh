#!/usr/bin/env bash
# Bash wrapper for the OBINexus TypeScript dependency updater.
#
# Usage examples:
#   ./update-typescript-deps.sh --dry-run
#   ./update-typescript-deps.sh --verbose
#   ./update-typescript-deps.sh --install --legacy-peer-deps
#   ./update-typescript-deps.sh --workspace ./obix --typescript-version 5.4.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/update-typescript-deps.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: update-typescript-deps.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3 was not found in PATH." >&2
    exit 1
fi

ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            ARGS+=("--dry-run")
            echo "[DRY RUN MODE] Changes will be reported but not applied"
            shift
            ;;
        --verbose|-v)
            ARGS+=("--verbose")
            shift
            ;;
        --install)
            ARGS+=("--install")
            shift
            ;;
        --legacy-peer-deps)
            ARGS+=("--legacy-peer-deps")
            shift
            ;;
        --workspace|--typescript-version|--npm-timeout)
            if [[ $# -lt 2 ]]; then
                echo "Error: $1 requires a value" >&2
                exit 2
            fi
            ARGS+=("$1" "$2")
            shift 2
            ;;
        --help|-h)
            exec "$PYTHON_BIN" "$PYTHON_SCRIPT" --help
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

echo "Starting OBINexus TypeScript Dependency Updater..."
"$PYTHON_BIN" "$PYTHON_SCRIPT" "${ARGS[@]}"

echo "Done!"
