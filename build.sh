#!/bin/bash
# ──────────────────────────────────────────
#  bb-dl build script
#  Run this any time you update bb-dl.py
#  Usage: ./build.sh
# ──────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Building bb-dl..."
python3 -m PyInstaller bb-dl.spec --noconfirm

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build complete! Binary is at: $SCRIPT_DIR/dist/bb-dl"
    echo "   Just type 'bb-dl' in your terminal to use it."
else
    echo ""
    echo "❌ Build failed. Check the output above for errors."
    exit 1
fi
