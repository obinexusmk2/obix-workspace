#!/bin/bash
# Bash wrapper for TypeScript dependency updater
# Usage: ./update-typescript-deps.sh [--dry-run] [--verbose] [--install]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/update-typescript-deps.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: update-typescript-deps.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Build arguments
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --dry-run)
            ARGS+=("--dry-run")
            echo "🔵 [DRY RUN MODE] Changes will be reported but not applied"
            ;;
        --verbose|-v)
            ARGS+=("--verbose")
            ;;
        --install)
            INSTALL=true
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 1
            ;;
    esac
done

# Run the Python script
echo "🚀 Starting OBINexus TypeScript Dependency Updater..."
python3 "$PYTHON_SCRIPT" "${ARGS[@]}"
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "❌ Script failed with exit code $EXIT_CODE" >&2
    exit $EXIT_CODE
fi

# Optionally run full workspace install
if [[ "$INSTALL" == true ]]; then
    echo ""
    echo "🔵 Running full workspace npm install..."
    npm install --legacy-peer-deps
fi

echo "✅ Done!"
