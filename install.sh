#!/bin/bash
# ──────────────────────────────────────────────────────
#  bb-ani installer
#  Run once: ./install.sh
#  After that, just type 'bb-ani' in any terminal.
#  No rebuilding needed — edits to bb-ani.py are live
#  instantly because we install a tiny launcher wrapper.
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="/usr/local/bin/bb-ani"

echo "📦 Installing bb-ani launcher to $TARGET ..."

sudo tee "$TARGET" > /dev/null << EOF
#!/bin/bash
exec python3 "$SCRIPT_DIR/bb-ani.py" "\$@"
EOF

sudo chmod +x "$TARGET"

if command -v bb-ani &>/dev/null; then
    echo ""
    echo "✅ Done! You can now type 'bb-ani' in any terminal."
else
    echo ""
    echo "❌ Something went wrong — bb-ani is still not in PATH."
    echo "   You may need to log out and back in, or check /usr/local/bin is in your PATH."
fi

