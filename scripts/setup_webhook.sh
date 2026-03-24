#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "Error: .env not found. Copy .env.example to .env and fill in first."
  exit 1
fi

# Load env
set -a
source .env
set +a

if [[ -z "${PUBLIC_BOT_TOKEN:-}" ]]; then
  echo "PUBLIC_BOT_TOKEN is required"
  exit 1
fi
if [[ -z "${WEBHOOK_URL:-}" ]]; then
  echo "WEBHOOK_URL is required"
  exit 1
fi

echo "Setting Telegram webhook to ${WEBHOOK_URL}"

curl -s -X POST "https://api.telegram.org/bot${PUBLIC_BOT_TOKEN}/setWebhook" \
  -F "url=${WEBHOOK_URL}" \
  -F "secret_token=${WEBHOOK_SECRET_TOKEN:-}" \
  -F 'allowed_updates=["message","edited_channel_post","callback_query"]' \
  -o webhook_response.json

cat webhook_response.json | jq .

if grep -q '"ok":true' webhook_response.json; then
  echo "Webhook set successfully"
  exit 0
else
  echo "Webhook failed"
  exit 2
fi
