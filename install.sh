#!/bin/bash

set -e

echo "[*] Updating Homebrew..."
brew update

echo "[*] Installing core dependencies..."
brew install go python3 git wget curl openssl nmap jq ruby

echo "[*] Creating Go bin directory..."
mkdir -p "$HOME/go/bin"
export GOPATH="$HOME/go"
export PATH="$PATH:$HOME/go/bin"

#######################################
# RECON TOOLS
#######################################

echo "[*] Installing subfinder..."
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

echo "[*] Installing hakrevdns..."
go install github.com/hakluke/hakrevdns@latest

echo "[*] Installing assetfinder..."
go install github.com/tomnomnom/assetfinder@latest

echo "[*] Installing hakrawler..."
go install github.com/hakluke/hakrawler@latest

echo "[*] Installing naabu..."
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

echo "[*] Installing dnsx..."
go install github.com/projectdiscovery/dnsx/v2/cmd/dnsx@latest

echo "[*] Installing amass..."
brew install amass

echo "[*] Installing subjack..."
go install github.com/haccer/subjack@latest

echo "[*] Installing httprobe..."
go install github.com/tomnomnom/httprobe@latest


#######################################
# WEB & SSL TOOLS
#######################################

echo "[*] Installing wafw00f..."
pip3 install wafw00f

echo "[*] Installing dirsearch..."
git clone https://github.com/maurosoria/dirsearch.git "$HOME/dirsearch"
sudo ln -sf "$HOME/dirsearch/dirsearch.py" /usr/local/bin/dirsearch

echo "[*] Installing testssl..."
git clone --depth 1 https://github.com/drwetter/testssl.sh.git "$HOME/testssl"
sudo ln -sf "$HOME/testssl/testssl.sh" /usr/local/bin/testssl

echo "[*] Installing jaeles..."
go install github.com/jaeles-project/jaeles@latest

echo "[*] Installing sslyze..."
pip3 install sslyze

echo "[*] Installing wfuzz..."
pip3 install wfuzz

echo "[*] Installing pshtt..."
pip3 install pshtt

echo "[*] Installing EyeWitness..."
git clone https://github.com/FortyNorthSecurity/EyeWitness.git "$HOME/EyeWitness"
cd "$HOME/EyeWitness/setup"
bash setup.sh
cd -

echo "[*] All tools installed successfully."

echo ""
echo "======================================="
echo " Done! Your Recon/Web/SSL toolkit is ready."
echo " Tools installed into:"
echo "   - Go binaries:        \$HOME/go/bin"
echo "   - Python tools:       pip3"
echo "   - Git cloned tools:   ~/dirsearch, ~/testssl, ~/EyeWitness"
echo "======================================="

