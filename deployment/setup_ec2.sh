#!/bin/bash
# EC2 Instance Setup Script for Job Scraper
# This script sets up a fresh EC2 instance with Docker and required dependencies

set -e  # Exit on error

echo "=========================================="
echo "EC2 Instance Setup for Job Scraper"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Update system packages
print_info "Updating system packages..."
apt-get update -y
apt-get upgrade -y
print_success "System packages updated"

# Install required packages
print_info "Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    vim \
    htop \
    ufw \
    fail2ban
print_success "Required packages installed"

# Install Docker
print_info "Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    print_success "Docker installed successfully"
else
    print_success "Docker already installed"
fi

# Verify Docker installation
docker --version
docker compose version

# Create application user
print_info "Creating application user..."
if ! id -u scraper &>/dev/null; then
    useradd -m -s /bin/bash scraper
    usermod -aG docker scraper
    print_success "User 'scraper' created and added to docker group"
else
    print_success "User 'scraper' already exists"
fi

# Create application directories
print_info "Creating application directories..."
mkdir -p /opt/scraper
mkdir -p /opt/scraper/data/{raw,processed,exports}
mkdir -p /opt/scraper/logs
mkdir -p /opt/scraper/config
mkdir -p /opt/scraper/backups

# Set ownership
chown -R scraper:scraper /opt/scraper
print_success "Application directories created"

# Configure firewall
print_info "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
print_success "Firewall configured"

# Configure fail2ban
print_info "Configuring fail2ban..."
systemctl start fail2ban
systemctl enable fail2ban
print_success "Fail2ban configured"

# Install Docker Compose (standalone - backup)
print_info "Installing Docker Compose standalone..."
DOCKER_COMPOSE_VERSION="v2.24.0"
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
print_success "Docker Compose standalone installed"

# Create swap file (recommended for t2.micro/small instances)
print_info "Creating swap file..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    print_success "2GB swap file created"
else
    print_success "Swap file already exists"
fi

# Configure Docker daemon
print_info "Configuring Docker daemon..."
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
systemctl restart docker
print_success "Docker daemon configured"

echo ""
echo "=========================================="
print_success "EC2 Instance Setup Complete!"
echo "=========================================="
echo ""
print_info "Next steps:"
echo "  1. Switch to scraper user: sudo su - scraper"
echo "  2. Clone your repository to /opt/scraper"
echo "  3. Configure environment variables (.env file)"
echo "  4. Run deployment script: ./deployment/deploy.sh"
echo ""

