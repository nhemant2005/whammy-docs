#!/bin/bash

# ==============================================================================
# WhammyDocs - Automated Linux VPS Deployment Script
# ==============================================================================
#
# Usage:
#   sudo bash deploy/setup-vps.sh
#
# This script automates:
#   1. System packages & Nginx installation
#   2. Creating a restricted 'whammy' system user
#   3. Cloning/copying project files to /var/www/whammy-docs
#   4. Setting up a Python venv & installing dependencies
#   5. Configuring DuckDNS with an automated cron job updater
#   6. Installing & activating the systemd service
#   7. Installing Nginx server block & suggesting Certbot SSL setup
#
# ==============================================================================

# Exit immediately if any command fails
set -e

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}======================================================================${NC}"
echo -e "${CYAN}                WhammyDocs VPS Setup & Deployment Script            ${NC}"
echo -e "${PURPLE}======================================================================${NC}"
echo ""

# Ensure the script is run with root privileges
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (using sudo).${NC}"
    echo -e "Please run: ${YELLOW}sudo bash deploy/setup-vps.sh${NC}"
    exit 1
fi

# Detect absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Interactive Prompts
echo -e "${YELLOW}>>> Configuration Prompts${NC}"
echo -e "To configure the server, please provide the following details:"
echo ""

# DuckDNS Domain
read -p "Enter your DuckDNS Subdomain name (e.g. 'whammydocs' for 'whammydocs.duckdns.org'): " DUCK_SUBDOMAIN
# Strip out duckdns.org if the user entered the full domain
DUCK_SUBDOMAIN=$(echo "$DUCK_SUBDOMAIN" | sed 's/\.duckdns\.org//g')
FULL_DOMAIN="${DUCK_SUBDOMAIN}.duckdns.org"

# DuckDNS Token
read -p "Enter your DuckDNS Token (from duckdns.org): " DUCK_TOKEN

# DeepSeek API Key
read -p "Enter your DeepSeek API Key: " DEEPSEEK_KEY

echo ""
echo -e "${GREEN}Thank you! Beginning deployment setup for domain: ${CYAN}${FULL_DOMAIN}${NC}"
echo ""

# ------------------------------------------------------------------------------
# 1. System Package Updates & Installation
# ------------------------------------------------------------------------------
echo -e "${YELLOW}1. Installing System Packages...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl cron
echo -e "${GREEN}✓ System packages installed successfully.${NC}"
echo ""

# ------------------------------------------------------------------------------
# 2. Creating the Secure 'whammy' User & Setup Directory
# ------------------------------------------------------------------------------
echo -e "${YELLOW}2. Setting up dedicated 'whammy' system user and folders...${NC}"

# Create 'whammy' system user if they don't already exist
if ! id -u whammy >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin whammy
    echo -e "Created restricted system user: ${GREEN}whammy${NC}"
else
    echo -e "User ${GREEN}whammy${NC} already exists."
fi

# Setup deployment directory
DEPLOY_DIR="/var/www/whammy-docs"
mkdir -p "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR/tmp"

# Copy project files from git repo to deployment directory
echo -e "Copying project files to ${BLUE}$DEPLOY_DIR${NC}..."
# Copy everything, but exclude virtual environments, cache files, etc.
rsync -av --exclude 'venv' \
          --exclude '.git' \
          --exclude '__pycache__' \
          --exclude '.pytest_cache' \
          --exclude '.env' \
          "$PROJECT_ROOT/" "$DEPLOY_DIR/"

echo -e "${GREEN}✓ Files successfully moved to $DEPLOY_DIR.${NC}"
echo ""

# ------------------------------------------------------------------------------
# 3. Python Virtual Environment & Dependency Installation
# ------------------------------------------------------------------------------
echo -e "${YELLOW}3. Creating Python Virtual Environment & Installing Dependencies...${NC}"
python3 -m venv "$DEPLOY_DIR/venv"
"$DEPLOY_DIR/venv/bin/pip" install --upgrade pip
"$DEPLOY_DIR/venv/bin/pip" install -r "$DEPLOY_DIR/requirements.txt"
echo -e "${GREEN}✓ Python virtual environment created and dependencies installed.${NC}"
echo ""

# ------------------------------------------------------------------------------
# 4. Configuring the Environment Secrets (.env)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}4. Configuring secrets in .env file...${NC}"
cat << EOF > "$DEPLOY_DIR/.env"
DEEPSEEK_API_KEY=${DEEPSEEK_KEY}
WHAMMY_TMP_DIR=/var/www/whammy-docs/tmp
EOF
echo -e "${GREEN}✓ Environment secrets written to $DEPLOY_DIR/.env.${NC}"
echo ""

# ------------------------------------------------------------------------------
# 5. Configuring DuckDNS Auto-Updater
# ------------------------------------------------------------------------------
echo -e "${YELLOW}5. Configuring DuckDNS Dynamic DNS client...${NC}"
DUCK_SCRIPT_DIR="/var/www/duckdns"
mkdir -p "$DUCK_SCRIPT_DIR"

# Write duckdns script
cat << EOF > "$DUCK_SCRIPT_DIR/duck.sh"
#!/bin/sh
echo url="https://www.duckdns.org/update?domains=${DUCK_SUBDOMAIN}&token=${DUCK_TOKEN}&ip=" | curl -k -o "$DUCK_SCRIPT_DIR/duck.log" -K -
EOF

chmod 700 "$DUCK_SCRIPT_DIR/duck.sh"

# Run it once immediately to point DuckDNS to the VPS IP
echo "Updating DuckDNS IP address..."
"$DUCK_SCRIPT_DIR/duck.sh"
DUCK_LOG_CONTENT=$(cat "$DUCK_SCRIPT_DIR/duck.log")

if [ "$DUCK_LOG_CONTENT" = "OK" ]; then
    echo -e "${GREEN}✓ DuckDNS successfully pointed to your VPS!${NC}"
else
    echo -e "${RED}Warning: DuckDNS response was '${DUCK_LOG_CONTENT}'. Double check your subdomain and token.${NC}"
fi

# Add cron job to update DuckDNS every 5 minutes
CRON_JOB="*/5 * * * * $DUCK_SCRIPT_DIR/duck.sh >/dev/null 2>&1"
(crontab -l 2>/dev/null | grep -Fv "duck.sh"; echo "$CRON_JOB") | crontab -
echo -e "${GREEN}✓ Cron job added: DuckDNS will auto-update VPS IP every 5 minutes.${NC}"
echo ""

# ------------------------------------------------------------------------------
# 6. Installing the Systemd Service
# ------------------------------------------------------------------------------
echo -e "${YELLOW}6. Installing systemd service daemon...${NC}"
cp "$DEPLOY_DIR/deploy/whammy-docs.service" /etc/systemd/system/whammy-docs.service

# Apply secure folder ownership to whammy user
chown -R whammy:whammy "$DEPLOY_DIR"
# Ensure nginx can read static files
chmod -R 755 "$DEPLOY_DIR/static"

# Reload systemd, enable and start service
systemctl daemon-reload
systemctl enable whammy-docs
systemctl restart whammy-docs

# Ensure the service is active and running
if systemctl is-active --quiet whammy-docs; then
    echo -e "${GREEN}✓ WhammyDocs systemd service is active and running!${NC}"
else
    echo -e "${RED}Error: WhammyDocs service failed to start. Run 'journalctl -u whammy-docs' for logs.${NC}"
    exit 1
fi
echo ""

# ------------------------------------------------------------------------------
# 7. Configuring Nginx Reverse Proxy
# ------------------------------------------------------------------------------
echo -e "${YELLOW}7. Deploying Nginx Server Block...${NC}"

# Replace domain placeholder in nginx template and write to sites-available
sed "s/YOUR_DOMAIN/${FULL_DOMAIN}/g" "$DEPLOY_DIR/deploy/nginx.conf" > "/etc/nginx/sites-available/whammy-docs"

# Enable Nginx block by making symlink to sites-enabled
ln -sf "/etc/nginx/sites-available/whammy-docs" "/etc/nginx/sites-enabled/"

# Remove default nginx site to avoid routing conflicts
rm -f /etc/nginx/sites-enabled/default

# Test configuration and reload Nginx
nginx -t
systemctl reload nginx
echo -e "${GREEN}✓ Nginx reverse proxy configured and reloaded!${NC}"
echo ""

# ------------------------------------------------------------------------------
# 8. Let's Encrypt SSL configuration suggestion
# ------------------------------------------------------------------------------
echo -e "${PURPLE}======================================================================${NC}"
echo -e "${GREEN}                  Deployment Foundation Complete!                     ${NC}"
echo -e "${PURPLE}======================================================================${NC}"
echo ""
echo -e "WhammyDocs is successfully running locally at ${CYAN}http://127.0.0.1:8000${NC}"
echo -e "and reverse proxied at ${CYAN}http://${FULL_DOMAIN}${NC}"
echo ""
echo -e "${YELLOW}FINAL CRITICAL STEP:${NC}"
echo -e "To configure automatic secure SSL (HTTPS) and complete the deployment, run:"
echo -e "  ${GREEN}sudo certbot --nginx -d ${FULL_DOMAIN}${NC}"
echo ""
echo -e "Certbot will automatically read the Nginx configuration, request the SSL certificates,"
echo -e "install them in Nginx, and activate permanent HTTP-to-HTTPS redirect."
echo ""
echo -e "Enjoy WhammyDocs!"
echo ""
