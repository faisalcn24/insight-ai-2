#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/insight-ai}"
APP_DIR="${APP_DIR:-$APP_ROOT/app}"
DATA_DIR="${DATA_DIR:-$APP_ROOT/data}"
ENV_FILE="${ENV_FILE:-$APP_ROOT/.env}"
REPO_URL="${REPO_URL:-https://github.com/faisalcn24/insight-ai-2.git}"
APP_USER="${APP_USER:-ubuntu}"
SWAP_FILE="${SWAP_FILE:-/swapfile}"
SWAP_SIZE="${SWAP_SIZE:-2G}"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this script as the ubuntu user, not root. It will use sudo where needed."
  exit 1
fi

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-venv nginx git

if [[ ! -f "$SWAP_FILE" ]]; then
  echo "Creating $SWAP_SIZE swap file at $SWAP_FILE..."
  sudo fallocate -l "$SWAP_SIZE" "$SWAP_FILE"
  sudo chmod 600 "$SWAP_FILE"
  sudo mkswap "$SWAP_FILE"
  sudo swapon "$SWAP_FILE"
  echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
else
  echo "Swap file already exists at $SWAP_FILE; leaving it unchanged."
fi

echo "Preparing app directories..."
sudo mkdir -p "$DATA_DIR" "$APP_DIR"
sudo chown -R "$APP_USER:$APP_USER" "$APP_ROOT"

if [[ -d "$APP_DIR/.git" ]]; then
  echo "Repository already exists. Pulling latest main..."
  git -C "$APP_DIR" pull --ff-only
else
  if [[ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "$APP_DIR is not empty and is not a Git repo. Move or empty it before running setup."
    exit 1
  fi
  echo "Cloning $REPO_URL..."
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "Creating Python virtual environment..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Creating $ENV_FILE from .env.example..."
  cp .env.example "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Edit $ENV_FILE and set GROQ_API_KEY before using the app."
else
  echo "$ENV_FILE already exists; leaving it unchanged."
fi

echo "Installing systemd and Nginx config..."
sudo cp deploy/insight-api.service /etc/systemd/system/
sudo cp deploy/insight-ui.service /etc/systemd/system/
sudo cp deploy/nginx-insight-ai.conf /etc/nginx/sites-available/insight-ai
sudo ln -sf /etc/nginx/sites-available/insight-ai /etc/nginx/sites-enabled/insight-ai
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now insight-api insight-ui nginx
sudo systemctl restart insight-api insight-ui
sudo systemctl reload nginx

echo "Setup complete."
echo "Check health with:"
echo "  curl http://127.0.0.1:8000/health"
echo "  curl http://127.0.0.1/api/health"
echo "If chat fails, confirm GROQ_API_KEY is set in $ENV_FILE, then run:"
echo "  sudo systemctl restart insight-api insight-ui"
