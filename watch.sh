#!/bin/bash
# ──────────────────────────────────────────────────────
#  bb-dl auto-rebuild watcher
#  Watches bb-dl.py and rebuilds automatically on save.
#  Usage: ./watch.sh
#  Stop:  Ctrl+C
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCH_FILE="$SCRIPT_DIR/bb-dl.py"

if ! command -v inotifywait &>/dev/null; then
    echo "❌ inotify-tools is not installed."
    echo "   Run: sudo pacman -S inotify-tools"
    exit 1
fi

echo "👁️  Watching bb-dl.py for changes... (Ctrl+C to stop)"
echo ""

while true; do
    inotifywait -e close_write "$WATCH_FILE" --quiet

    echo ""
    echo "📝 Change detected — rebuilding..."
    bash "$SCRIPT_DIR/build.sh"
    echo ""
    echo "👁️  Watching for next change..."
done
