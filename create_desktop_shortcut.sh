#!/bin/bash
# Install Aria Desktop Shortcut to Desktop and Applications Menu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOME/Desktop" "$HOME/.local/share/applications"

cp "$SCRIPT_DIR/Aria-Assistant.desktop" "$SCRIPT_DIR/Aria.desktop"
cp "$SCRIPT_DIR/Aria-Assistant.desktop" "$HOME/Desktop/Aria-Assistant.desktop"
cp "$SCRIPT_DIR/Aria.desktop" "$HOME/Desktop/Aria.desktop"
cp "$SCRIPT_DIR/Aria-Assistant.desktop" "$HOME/.local/share/applications/Aria-Assistant.desktop"
cp "$SCRIPT_DIR/Aria.desktop" "$HOME/.local/share/applications/Aria.desktop"

chmod +x "$HOME/Desktop/Aria-Assistant.desktop" "$HOME/Desktop/Aria.desktop" 2>/dev/null || true
chmod +x "$HOME/.local/share/applications/Aria-Assistant.desktop" "$HOME/.local/share/applications/Aria.desktop" 2>/dev/null || true
gio trust "$HOME/Desktop/Aria-Assistant.desktop" 2>/dev/null || true
gio trust "$HOME/Desktop/Aria.desktop" 2>/dev/null || true

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
touch "$HOME/.local/share/applications" 2>/dev/null || true
touch "$HOME/Desktop" 2>/dev/null || true

echo "✅ Desktop Launcher 'Aria' Created & Refreshed Successfully on Desktop & App Menu!"
