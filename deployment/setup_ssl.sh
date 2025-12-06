#!/bin/bash
# SSL Setup Script using Let's Encrypt
# Run this script after initial deployment to enable HTTPS

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

echo "=========================================="
echo "SSL Certificate Setup (Let's Encrypt)"
echo "=========================================="
echo ""

# Get domain name
read -p "Enter your domain name (e.g., api.example.com): " DOMAIN
read -p "Enter your email address: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    print_error "Domain and email are required!"
    exit 1
fi

print_info "Domain: $DOMAIN"
print_info "Email: $EMAIL"
echo ""
read -p "Is this correct? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    print_error "Aborted"
    exit 1
fi

# Install certbot
print_info "Installing certbot..."
apt-get update
apt-get install -y certbot
print_success "Certbot installed"

# Stop nginx temporarily
print_info "Stopping nginx..."
cd /opt/scraper
docker compose -f docker-compose.production.yml stop nginx
print_success "Nginx stopped"

# Get certificate
print_info "Obtaining SSL certificate..."
certbot certonly --standalone \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

if [ $? -eq 0 ]; then
    print_success "SSL certificate obtained!"
else
    print_error "Failed to obtain SSL certificate"
    docker compose -f docker-compose.production.yml start nginx
    exit 1
fi

# Create SSL directory
print_info "Setting up SSL directory..."
mkdir -p /opt/scraper/deployment/ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/scraper/deployment/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/scraper/deployment/ssl/
chown -R scraper:scraper /opt/scraper/deployment/ssl
chmod 600 /opt/scraper/deployment/ssl/*.pem
print_success "SSL certificates copied"

# Update nginx configuration
print_info "Updating nginx configuration..."
cat > /opt/scraper/deployment/nginx.conf.ssl <<'EOF'
# This is a template - update server_name with your domain
# Then replace deployment/nginx.conf with this file

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_status 429;

    upstream api_backend {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
    }

    # HTTP - Redirect to HTTPS
    server {
        listen 80;
        server_name DOMAIN_PLACEHOLDER;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name DOMAIN_PLACEHOLDER;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        location / {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;

            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /health {
            proxy_pass http://api_backend/health;
            access_log off;
        }
    }
}
EOF

# Replace domain placeholder
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /opt/scraper/deployment/nginx.conf.ssl

print_success "SSL nginx configuration created: deployment/nginx.conf.ssl"

# Setup auto-renewal
print_info "Setting up auto-renewal..."
cat > /etc/cron.d/certbot-renew <<EOF
0 3 * * * root certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/$DOMAIN/*.pem /opt/scraper/deployment/ssl/ && chown scraper:scraper /opt/scraper/deployment/ssl/*.pem && cd /opt/scraper && docker compose -f docker-compose.production.yml restart nginx"
EOF
print_success "Auto-renewal configured (daily at 3 AM)"

# Restart nginx
print_info "Starting nginx..."
docker compose -f docker-compose.production.yml start nginx
print_success "Nginx started"

echo ""
echo "=========================================="
print_success "SSL Setup Complete!"
echo "=========================================="
echo ""
print_info "Next steps:"
echo "  1. Review the SSL nginx config: /opt/scraper/deployment/nginx.conf.ssl"
echo "  2. Replace nginx.conf: mv deployment/nginx.conf.ssl deployment/nginx.conf"
echo "  3. Restart nginx: docker compose -f docker-compose.production.yml restart nginx"
echo "  4. Test HTTPS: curl https://$DOMAIN/health"
echo ""
print_info "Certificate will auto-renew every 60 days"
echo ""

