#!/usr/bin/env bash

echo "=========================="
echo " 1. Homebrew Installed"
echo "=========================="
brew list --formula
brew list --cask
echo

echo "=========================="
echo " 2. Python Packages (pip)"
echo "=========================="
pip3 list
echo

echo "=========================="
echo " 3. Go Binaries in GOPATH"
echo "=========================="
if [ -d "$(go env GOPATH)/bin" ]; then
    ls "$(go env GOPATH)/bin"
else
    echo "No GOPATH bin directory found."
fi
echo

echo "=========================="
echo " 4. AraUltra Project Tools"
echo "=========================="

PROJECT_DIR="$HOME/Desktop/AraUltra"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory not found: $PROJECT_DIR"
    exit 1
fi

echo
echo "-- Python imports in project:"
grep -Rho "import \S\+\\|from \S\+ import" "$PROJECT_DIR" 2>/dev/null \
    | sed 's/import //; s/from //; s/ import.*//' \
    | sort -u
echo

echo "-- Requirements file (if present):"
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    cat "$PROJECT_DIR/requirements.txt"
else
    echo "No requirements.txt found."
fi
echo

echo "-- Executables referenced in project:"
grep -Rho "\b(subfinder|naabu|dnsx|amass|ffuf|nuclei|assetfinder|hak.*|gowitness|testssl|dirsearch|wafw00f|pshtt|sslyze)\b" "$PROJECT_DIR" \
    | sort -u
echo

echo "=========================="
echo " 5. DIFF: Installed vs. Project Needs"
echo "=========================="

# Installed tools list
INSTALLED_TOOLS=$(mktemp)
{
    brew list --formula
    pip3 list | awk '{print $1}'
    ls "$(go env GOPATH)/bin" 2>/dev/null
} | sort -u > "$INSTALLED_TOOLS"

# Project referenced tools list
PROJECT_TOOLS=$(mktemp)
{
    grep -Rho "\b(subfinder|naabu|dnsx|amass|ffuf|nuclei|assetfinder|hak.*|gowitness|testssl|dirsearch|wafw00f|pshtt|sslyze)\b" "$PROJECT_DIR"
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        awk '{print $1}' "$PROJECT_DIR/requirements.txt"
    fi
} | sort -u > "$PROJECT_TOOLS"

echo "-- Tools Missing (project expects but not installed):"
comm -23 "$PROJECT_TOOLS" "$INSTALLED_TOOLS"
echo

echo "-- Tools Extra (installed but not in project):"
comm -13 "$PROJECT_TOOLS" "$INSTALLED_TOOLS"
echo

rm "$INSTALLED_TOOLS" "$PROJECT_TOOLS"

echo "=========================="
echo " AUDIT COMPLETE "
echo "=========================="

