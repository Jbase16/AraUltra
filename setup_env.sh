#!/bin/bash
# AraUltra Bootstrap Script
# Sets up Python environment with modern dependencies (cryptography, httpx, curl_cffi)

set -e

echo "[*] Bootstrapping AraUltra Environment..."

# Check Python version
python3 -c "import sys; exit(0) if sys.version_info >= (3, 11) else exit(1)" || {
    echo "[-] Error: Python 3.11+ required (3.14 recommended)"
    exit 1
}

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "[*] Upgrading pip..."
pip install --upgrade pip

echo "[*] Installing dependencies..."
pip install -r requirements.txt

echo "[+] Setup complete! Activate with: source venv/bin/activate"
