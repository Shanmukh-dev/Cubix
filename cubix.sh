SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
uv run --directory "$SCRIPT_DIR/." main.py --cwd "$PWD"