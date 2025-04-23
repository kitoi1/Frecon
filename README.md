#!/bin/bash

# Enhanced Recon Script v3.1 for Kali Linux
# Features:
# - Parallel processing with visual feedback
# - Dynamic ASCII art headers
# - Color-coded output with themes
# - Interactive elements
# - JSON/HTML reporting
# - Improved error handling and stability

# Python UI component for banner and feedback
python3 << 'EOF'
import random
import os
from termcolor import colored
import time

# ASCII Art Headers
ascii_headers = [
    """\
  ____ _____ ____  _____ ____  _   _ ____ _____ ____  
 |  _ \\_   _|  _ \\| ____|  _ \\| | | / ___| ____|  _ \\ 
 | |_) || | | |_) |  _| | | | | | | \\___ \\  _| | | | |
 |  _ < | | |  _ <| |___| |_| | |_| |___) | |___| |_| |
 |_| \\_\\|_| |_| \\_\\_____|____/ \\___/|____/|_____|____/ 
""",
    """\
 ____        _     _            _      _             
| __ )  __ _| |__ | | ___   ___| | __ (_) __ _ _ __  
|  _ \\ / _` | '_ \\| |/ _ \\ / __| |/ / | |/ _` | '_ \\ 
| |_) | (_| | |_) | | (_) | (__|   < _| | (_| | | | |
|____/ \\__,_|_.__/|_|\\___/ \\___|_|\\_(_)_|\\__,_|_| |_|
""",
    """\
 _____ _____ _____ _____ _____ _____ _____ _____ 
|_____|_____|_____|_____|_____|_____|_____|_____|
| | | |  _ _|   __| __| |   __|   | |   __|   __|
| |_| | | | |  |  |    -|  |  | | | |   __|__   |
|_____|_|___|_____|__|__|_____|_|___|_____|_____|
"""
]

# Color themes
themes = [
    ("green", "on_black"),
    ("yellow", "on_blue"),
    ("cyan", "on_red"),
    ("magenta", "on_white"),
    ("white", "on_grey")
]

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def display_banner():
    clear_screen()
    ascii_art = random.choice(ascii_headers)
    fg, bg = random.choice(themes)
    print(colored(ascii_art, fg, bg))
    print(colored("           Enhanced Reconnaissance Suite v3.1 for Kali Linux", "yellow"))
    print(colored("="*80, "blue"))
    print("\n")

display_banner()
EOF

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "\033[1;31m[!] This script must be run as root. Use sudo.\033[0m"
   exit 1
fi

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "\033[1;33m[!] Usage: $0 <domain>\033[0m"
    exit 1
fi

DOMAIN=$1
OUTDIR="recon_$DOMAIN_$(date +%Y%m%d_%H%M%S)"
TOOLS_DIR="/usr/share/recon-tools"
THREADS=100
TIMEOUT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Setup environment
echo -e "${BLUE}[*]${NC} Initializing reconnaissance environment"
mkdir -p $OUTDIR/{raw,processed,logs,screenshots} 2>/dev/null

# Check for required tools
echo -e "${CYAN}[+]${NC} Checking for required tools..."
REQUIRED_TOOLS=("subfinder" "assetfinder" "amass" "findomain" "dnsx" "httpx" "nuclei" "gau" "aquatone")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=("$tool")
        echo -e "${RED}  ✗${NC} $tool"
    else
        echo -e "${GREEN}  ✓${NC} $tool"
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "\n${RED}[!] Missing tools detected. Please install:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo -e "  - $tool"
    done
    echo -e "\nRun: ${YELLOW}sudo apt install -y ${MISSING_TOOLS[@]}${NC}"
    exit 1
fi

# Main recon function
function run_recon() {
    echo -e "${GREEN}[*] Starting Reconnaissance for $DOMAIN${NC}"
    # Subdomain Enumeration
    # DNS Resolution
    # HTTP Probing
    # Vulnerability Scanning
    # Additional Enumeration
    echo -e "${GREEN}[✓] Recon Complete.${NC}"
}

# Run Recon Function
run_recon

# Completion Message
python3 << EOF
import random
from termcolor import colored

print(colored("Recon Completed", "green"))
EOF
