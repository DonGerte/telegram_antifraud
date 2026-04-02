# Telegram Anti-Fraud System

**Production-ready reference implementation** for detecting and mitigating malicious operators in Telegram (spam, raids, scams, multi-accounting).

[![GitHub CI](https://github.com/DonGerte/telegram_antifraud/actions/workflows/ci.yml/badge.svg)](https://github.com/DonGerte/telegram_antifraud/actions) ![GitHub Release](https://img.shields.io/github/v/release/DonGerte/telegram_antifraud?style=flat&label=Release) [![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Status:** ✅ **PRODUCTION READY** – Completo antifraud system con risk scoring, strikes, memory y admin controls
**License:** MIT – See [LICENSE](LICENSE)
**Last Updated:** April 2026

---

## 🚀 ¿Qué hace este proyecto?

- Monitoriza mensajes de Telegram con un motor de riesgo que detecta spam, raid, fraude y multi-cuentas.
- Aplica reglas automáticas de mitigación (ban, mute, throttle) basadas en comportamiento y heurísticas.
- Provee un bot privado de administración con comandos `/ban`, `/unban`, `/stats`, y más.
- Dispone de persistencia híbrida: SQLite (Pyrogram session), JSON para perfiles y opcional Postgres/Redis.

---

## ⚙️ Estructura del proyecto

```
telegram_antifraud/
├── bots/
│   ├── public_bot.py
│   ├── private_bot.py
│   └── userbot.py
├── engine/
│   ├── risk_assessment.py
│   ├── scoring.py
│   ├── clusters.py
│   ├── honeypot.py
│   ├── raid.py
│   ├── signals.py
│   └── logger.py
├── services/
│   ├── db.py
│   ├── memory.py
│   ├── ban_manager.py
│   ├── strike_manager.py
│   └── user_history.py
├── tests.py
├── requirements.txt
├── docker-compose.yml
├── start_bots.ps1
├── config.py
├── .env (local)
└── README.md
```

---

## 🛠️ Requisitos

- Python 3.10+ (recomendado 3.13)
- Redis (opcional para cola internamente, pero recomendado)
- Telegram bots con token y API ID/API HASH
- Dependencias Python: `pip install -r requirements.txt`

---

## 🧩 Configuración

1. Clona el repo:
   ```bash
   git clone https://github.com/DonGerte/telegram_antifraud.git
   cd telegram_antifraud
   ```
2. Crea y activa virtualenv:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # Windows
   source .venv/bin/activate       # Linux/Mac
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Crea `.env`:
   ```ini
   PUBLIC_BOT_TOKEN=<token_public>
   PRIVATE_BOT_TOKEN=<token_priv>
   API_ID=<api_id>
   API_HASH=<api_hash>
   REDIS_URL=redis://localhost:6379/0
   ADMIN_IDS=<tu_id>,<otro_id>
   ```

---

## ▶️ Arranque manual de bots (modo senior)

### 1) Iniciar Redis (opcional pero recomendado)

Windows (si instalado con chocolatey):
```powershell
redis-server
```

Docker:
```bash
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
```

### 2) Ejecutar bot público

```powershell
cd C:\workspace	elegram_antifraud
.\.venv\Scripts\python.exe bots\public_bot.py
```

### 3) Ejecutar bot privado

```powershell
cd C:\workspace	elegram_antifraud
.\.venv\Scripts\python.exe bots\private_bot.py
```

### 4) Comandos de smoke test (private)

- `/whoami` -> muestra tu ID + ADMIN_IDS
- `/start` -> muestra interfaz admin
- `/stats` -> estadísticas básicas

---

## 🧪 Modo de prueba local (sin conexión en pelado)

```bash
.\.venv\Scripts\python.exe bots\private_bot.py --test-mode
.\.venv\Scripts\python.exe bots\public_bot.py --test-mode
```

---

## 🧾 Git: commits + push (recomendado)

```bash
git status
git add .
git commit -m "fix: session lock + in-memory fallback + README senior runbook"
git push origin main
```

---

## 📌 Notas de despliegue senior

- Production: ejecutar con contenedores y supervisión de logs
- Asegurar tokens en secret manager
- Usar Redis persistente y backups de `store.json`
- Monitorizar latencia de Pyrogram y uso CPU
- Registrar eventos clave con `engine.logger.log_event`
