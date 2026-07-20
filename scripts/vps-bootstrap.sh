#!/usr/bin/env bash
# Run on a fresh Ubuntu 22.04/24.04 VPS as root (or with sudo).
# Usage: bash scripts/vps-bootstrap.sh

set -euo pipefail

echo "==> Updating system packages"
apt update
apt upgrade -y

echo "==> Installing base packages"
apt install -y \
  git \
  curl \
  ufw \
  nginx \
  redis-server \
  postgresql \
  postgresql-contrib \
  ffmpeg \
  build-essential

echo "==> Enabling Redis + Postgres"
systemctl enable --now redis-server
systemctl enable --now postgresql

echo "==> Firewall (SSH + HTTP/HTTPS)"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> Bootstrap done"
echo
echo "Next:"
echo "  1. Create a non-root user (optional): adduser notely && usermod -aG sudo notely"
echo "  2. Install uv + Node"
echo "  3. Create Postgres DB/user"
echo "  4. Clone Notely and configure .env"
echo
echo "Quick checks:"
redis-cli ping
sudo -u postgres psql -c 'SELECT version();'
ffmpeg -version | head -n 1
nginx -v
echo "OK"
