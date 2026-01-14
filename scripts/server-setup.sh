#!/bin/bash

# ===========================================
# Poker MTT Helper - Server Setup Script
# ===========================================
# This script installs all required dependencies on a fresh Ubuntu server
# Run as root or with sudo: sudo ./scripts/server-setup.sh

set -e

echo "🎰 Poker MTT Helper - Server Setup"
echo "==================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

echo "📋 Detected OS: $OS $VER"
echo ""

# ===========================================
# Update system
# ===========================================
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# ===========================================
# Install basic dependencies
# ===========================================
echo "📦 Installing basic dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release

# ===========================================
# Configure firewall
# ===========================================
echo "🔒 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
echo "✅ Firewall configured"

# ===========================================
# Install Docker
# ===========================================
echo "🐳 Installing Docker..."

# Remove old versions
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

echo "✅ Docker installed: $(docker --version)"

# ===========================================
# Create app user
# ===========================================
APP_USER="pokerhelper"
echo "👤 Creating application user: $APP_USER"

if id "$APP_USER" &>/dev/null; then
    echo "User $APP_USER already exists"
else
    useradd -m -s /bin/bash $APP_USER
    usermod -aG docker $APP_USER
    echo "✅ User $APP_USER created and added to docker group"
fi

# ===========================================
# Create directories
# ===========================================
echo "📁 Creating directories..."
mkdir -p /var/backups/pokerhelper
mkdir -p /var/log/pokerhelper
chown -R $APP_USER:$APP_USER /var/backups/pokerhelper
chown -R $APP_USER:$APP_USER /var/log/pokerhelper

# ===========================================
# Configure fail2ban
# ===========================================
echo "🔐 Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

systemctl restart fail2ban
echo "✅ fail2ban configured"

# ===========================================
# Install NVIDIA drivers (optional)
# ===========================================
read -p "🎮 Do you want to install NVIDIA drivers for GPU support? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Installing NVIDIA drivers..."
    apt-get install -y nvidia-driver-535
    
    # Install NVIDIA Container Toolkit
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    apt-get update
    apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
    
    echo "✅ NVIDIA drivers and container toolkit installed"
    echo "⚠️  A reboot is required for GPU support"
fi

# ===========================================
# Summary
# ===========================================
echo ""
echo "==================================="
echo "✅ Server setup complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Clone the repository:"
echo "   sudo -u $APP_USER git clone <repo> /home/$APP_USER/pokerhelper"
echo ""
echo "2. Configure environment:"
echo "   cd /home/$APP_USER/pokerhelper"
echo "   cp env.example .env.production"
echo "   nano .env.production"
echo ""
echo "3. Setup SSL (if you have a domain):"
echo "   ./scripts/ssl-setup.sh your-domain.com"
echo ""
echo "4. Deploy the application:"
echo "   ./deploy.sh prod"
echo ""
