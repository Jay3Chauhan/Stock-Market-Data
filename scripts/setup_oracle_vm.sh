#!/bin/bash
# NSE Scraper - Oracle Cloud VM Setup Script
# Run this script on a fresh Oracle Cloud Ubuntu VM

set -e  # Exit on error

echo "=========================================="
echo "NSE Scraper - Oracle Cloud Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please run this script as a normal user, not root"
    exit 1
fi

# Step 1: Update system
log_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker
log_info "Installing Docker..."
if command -v docker &> /dev/null; then
    log_warn "Docker is already installed"
else
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log_info "Docker installed successfully"
fi

# Step 3: Install Docker Compose
log_info "Installing Docker Compose..."
if command -v docker-compose &> /dev/null; then
    log_warn "Docker Compose is already installed"
else
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose installed successfully"
fi

# Step 4: Install additional tools
log_info "Installing additional tools..."
sudo apt install -y git curl htop nano

# Step 5: Configure firewall
log_info "Configuring firewall..."
sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 1020 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT

# Save iptables rules
sudo apt install -y iptables-persistent
sudo netfilter-persistent save

# Step 6: Set timezone to IST
log_info "Setting timezone to IST..."
sudo timedatectl set-timezone Asia/Kolkata

# Step 7: Clone repository (if not exists)
if [ ! -d "$HOME/NSE-Scraper" ]; then
    log_info "Cloning NSE-Scraper repository..."
    cd $HOME
    git clone https://github.com/anv-het/NSE-Scraper.git
else
    log_warn "NSE-Scraper directory already exists"
fi

# Step 8: Create production config
cd $HOME/NSE-Scraper
if [ ! -f "config.production.ini" ]; then
    log_info "Creating production config from template..."
    cp config.production.template.ini config.production.ini
    log_warn "Please edit config.production.ini with your MongoDB Atlas URI"
else
    log_warn "config.production.ini already exists"
fi

# Step 9: Create .env file
if [ ! -f ".env" ]; then
    log_info "Creating .env file from template..."
    cp .env.template .env
    log_warn "Please edit .env with your MongoDB Atlas URI"
else
    log_warn ".env file already exists"
fi

# Step 10: Create systemd service
log_info "Creating systemd service..."
sudo tee /etc/systemd/system/nse-scraper.service > /dev/null <<EOF
[Unit]
Description=NSE Scraper Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$HOME/NSE-Scraper
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable nse-scraper

# Step 11: Setup keep-alive cron job
log_info "Setting up keep-alive cron job..."
(crontab -l 2>/dev/null; echo "0 * * * * curl -s http://localhost:1020/health > /dev/null 2>&1") | crontab -

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Edit configuration files:"
echo "   nano $HOME/NSE-Scraper/config.production.ini"
echo "   nano $HOME/NSE-Scraper/.env"
echo ""
echo "2. Update MongoDB Atlas URI in both files"
echo ""
echo "3. IMPORTANT: Log out and log back in for Docker group changes"
echo "   exit"
echo ""
echo "4. After logging back in, deploy the application:"
echo "   cd $HOME/NSE-Scraper"
echo "   docker-compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "5. Check status:"
echo "   docker-compose -f docker-compose.prod.yml ps"
echo "   curl http://localhost:1020/health"
echo ""
echo "=========================================="
