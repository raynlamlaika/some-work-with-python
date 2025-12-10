#!/bin/bash

# Fix permissions inside venv
echo "[*] Fixing venv permissions..."

VENVDIR="./venv"

if [ ! -d "$VENVDIR" ]; then
    echo "[!] venv not found in current directory."
    exit 1
fi

# Give user full permissions
chmod -R u+rwX "$VENVDIR"

echo "[*] Upgrading pip..."
"$VENVDIR/bin/pip" install --upgrade pip

echo "[*] Reinstalling black..."
"$VENVDIR/bin/pip" install black --no-cache-dir

echo "[+] Done."
