# Telegram Webhook Deployment (Full-stack)

Esta guía cubre el despliegue recomendado para un bot de Telegram en **modo webhook** en producción.

## Requisitos previos

- Dominio con HTTPS (LetsEncrypt/Cloudflare)
- Redis + PostgreSQL operativos
- Token de BotFather (`PUBLIC_BOT_TOKEN`)
- `WEBHOOK_SECRET_TOKEN` generado y seguro
- Pines de puertos abiertos o Ingress configurado

## 1. Configurar `.env`

Copia `.env.example` a `.env` y completa:

- `PUBLIC_BOT_TOKEN`
- `PRIVATE_BOT_TOKEN` (si aplica)
- `REDIS_URL`
- `DATABASE_URL`
- `WEBHOOK_URL` (ej: `https://bot.tu-dominio.com/webhook`)
- `WEBHOOK_SECRET_TOKEN` (valor largo)

## 2. Iniciar servicios (Docker Compose)

```bash
cd /ruta/a/telegram_antifraud
docker compose pull
docker compose up -d

# verificar
docker compose ps
```

## 3. Configurar webhook en Telegram

```bash
cd /ruta/a/telegram_antifraud
chmod +x scripts/setup_webhook.sh
./scripts/setup_webhook.sh
```

Verifica:

```bash
curl "https://api.telegram.org/bot${PUBLIC_BOT_TOKEN}/getWebhookInfo"
```

## 4. Verificar endpoint y salud

- `GET /healthz` debe devolver `{ "status": "ok" }`
- `POST /webhook` con payload de prueba

## 5. Comprobar que llegan eventos Redis

- Examina `redis-cli`:
  - `LLEN data_bus`
  - `LLEN action_bus`

## 6. Ajustes del flujo de trabajo

- `webhook_api` expone `8000` en `docker-compose`
- `public_bot` sigue disponible en polling (fallback)
- `worker` consume de `data_bus` y envía acciones a `action_bus`

## 7. Monitoreo

- Worker expone métricas en `8001` (Prometheus) y `worker_messages_processed_total`.
- Agrega alertas sobre `worker_errors_total`, `data_bus` queue depth y 5xx refrescos.
