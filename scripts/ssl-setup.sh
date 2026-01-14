#!/bin/bash

# ===========================================
# Poker MTT Helper - SSL Setup Script
# ===========================================
# This script obtains SSL certificates from Let's Encrypt
# Usage: ./scripts/ssl-setup.sh your-domain.com [email@example.com]

set -e

DOMAIN=$1
EMAIL=${2:-admin@$DOMAIN}

echo "🔐 Poker MTT Helper - SSL Setup"
echo "================================"
echo ""

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain> [email]"
    echo "Example: $0 poker.example.com admin@example.com"
    exit 1
fi

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo $0 $DOMAIN $EMAIL"
    exit 1
fi

# ===========================================
# Install Certbot
# ===========================================
echo "📦 Installing Certbot..."
apt-get update
apt-get install -y certbot python3-certbot-nginx

# ===========================================
# Stop any running services on port 80
# ===========================================
echo "⏹️ Stopping services on port 80..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# ===========================================
# Obtain certificate
# ===========================================
echo "🔑 Obtaining SSL certificate..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --domain "$DOMAIN" \
    --preferred-challenges http

# ===========================================
# Create SSL directory and copy certificates
# ===========================================
SSL_DIR="$(dirname "$0")/../nginx/ssl"
mkdir -p "$SSL_DIR"

echo "📋 Copying certificates..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$SSL_DIR/"
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$SSL_DIR/"
chmod 600 "$SSL_DIR"/*.pem

# ===========================================
# Setup auto-renewal
# ===========================================
echo "🔄 Setting up auto-renewal..."

# Create renewal hook script
cat > /etc/letsencrypt/renewal-hooks/deploy/pokerhelper.sh << EOF
#!/bin/bash
# Copy renewed certificates
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/
chmod 600 $SSL_DIR/*.pem

# Reload nginx
cd $(dirname "$0")/../..
docker compose -f docker-compose.prod.yml exec -T nginx nginx -s reload 2>/dev/null || true
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/pokerhelper.sh

# Setup cron for renewal
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | crontab -

# ===========================================
# Update nginx config
# ===========================================
echo "📝 Updating nginx configuration..."
NGINX_CONF="$(dirname "$0")/../nginx/nginx.conf"

# Update domain in nginx config
sed -i "s/server_name _;/server_name $DOMAIN;/g" "$NGINX_CONF"

# ===========================================
# Summary
# ===========================================
echo ""
echo "================================"
echo "✅ SSL Setup Complete!"
echo "================================"
echo ""
echo "Certificates location:"
echo "  - $SSL_DIR/fullchain.pem"
echo "  - $SSL_DIR/privkey.pem"
echo ""
echo "Auto-renewal: Configured (daily at 3:00 AM)"
echo ""
echo "Now you can deploy with HTTPS:"
echo "  ./deploy.sh prod"
echo ""
