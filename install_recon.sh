#!/usr/bin/env bash
set +o histexpand
set -e

echo "======================================="
echo " AraUltra Recon/Web/SSL Installer"
echo " Modern macOS-Compatible Toolchain"
echo "======================================="

echo "[*] Updating Homebrew..."
brew update

echo "[*] Installing core dependencies..."
brew install go python@3.14 git wget curl jq nmap

echo "[*] Ensuring Go bin directory exists..."
mkdir -p "$HOME/go/bin"

export PATH="$HOME/go/bin:$PATH"

###############################################
# Go-Based Tools (fast, modern, no breakage)
###############################################

echo "[*] Installing subfinder..."
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

echo "[*] Installing assetfinder..."
go install github.com/tomnomnom/assetfinder@latest

echo "[*] Installing hakrevdns..."
go install github.com/hakluke/hakrevdns@latest

echo "[*] Installing hakrawler..."
go install github.com/hakluke/hakrawler@latest

echo "[*] Installing naabu..."
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

echo "[*] Installing dnsx..."
go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest

echo "[*] Installing httpx..."
go install github.com/projectdiscovery/httpx/cmd/httpx@latest

echo "[*] Installing gowitness (screenshots)..."
go install github.com/sensepost/gowitness@latest


###############################################
# Python-based tools (pure Python only)
###############################################

echo "[*] Installing sslyze..."
pip3 install --upgrade sslyze

echo "[*] Installing wafw00f..."
pip3 install --upgrade wafw00f

echo "[*] Installing wfuzz..."
pip3 install --upgrade wfuzz


###############################################
# Git-based tools (no compilation)
###############################################

echo "[*] Installing dirsearch..."
git clone https://github.com/maurosoria/dirsearch.git "$HOME/dirsearch"

echo "[*] Installing testssl.sh..."
git clone --depth 1 https://github.com/drwetter/testssl.sh.git "$HOME/testssl"


###############################################
# Summary
###############################################

echo ""
echo "======================================="
echo " Installation Complete!"
echo " Tools installed to:"
echo "   Go binaries:        $HOME/go/bin"
echo "   Python tools:       pip3 site-packages"
echo "   Git tools:          ~/dirsearch, ~/testssl"
echo "======================================="
echo " All tools are macOS-safe and modern."
echo "======================================="

