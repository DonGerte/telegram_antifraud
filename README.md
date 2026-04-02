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

## ▶️ Arranque de bots (modo senior)

### ⚡ Opción 1: Usar launcher profesional (RECOMENDADO)

Inicia ambos bots con supervisión automática, monitoreo de crashes y logs centralizados:

```powershell
cd C:\workspace\telegram_antifraud
.\.venv\Scripts\python.exe start_bots.py
```

**Características:**
- ✅ Solo una instancia de cada bot ejecutándose (mutex file-based)
- ✅ Reinicio automático si un bot crashea
- ✅ Logs centralizados con timestamps
- ✅ Shutdown graceful con Ctrl+C
- ✅ Soporte para flags `--verbose` y `--no-monitor`

**Ejemplos:**
```powershell
# Verbose logging + monitoring
.\.venv\Scripts\python.exe start_bots.py --verbose

# Solo bot privado
.\.venv\Scripts\python.exe start_bots.py --mode private-only

# Solo bot público
.\.venv\Scripts\python.exe start_bots.py --mode public-only

# Sin monitoreo (manual restart)
.\.venv\Scripts\python.exe start_bots.py --no-monitor
```

---

### 🔧 Opción 2: Ejecutar bots individualmente

**Bot Público (monitorea mensajes de grupo):**
```powershell
cd C:\workspace\telegram_antifraud
.\.venv\Scripts\python.exe bots\public_bot.py --verbose
```

**Bot Privado (admin commands):**
```powershell
cd C:\workspace\telegram_antifraud
.\.venv\Scripts\python.exe bots\private_bot.py --verbose
```

**⚠️ IMPORTANTE:** 
- No ejecutes dos instancias de public_bot o private_bot simultáneamente
- Si intenta hacerlo, obtendrás error: `"Another instance of [bot] is already running"`
- Usa `Ctrl+C` para shutdown limpio

---

### 🧪 Modo Test (sin conexión a Telegram)

```powershell
# Test bot privado (valida funciones admin)
.\.venv\Scripts\python.exe bots\private_bot.py --test-mode

# Test bot público (valida procesamiento de mensajes)
.\.venv\Scripts\python.exe bots\public_bot.py --test-mode
```

Esto ejecuta suite de tests sin conectar a Telegram:
- ✓ Importaciones correctas
- ✓ Sistema de memoria funcional
- ✓ Sistema de strikes
- ✓ Risk assessment motor
- ✓ Ban manager

---

### ☁️ Opción 3: Redis (para cola de acciones inter-bot)

```powershell
# Terminal 1: Redis
docker run -d --name antifraud-redis -p 6379:6379 redis:7-alpine

# Terminal 2: Bot público
.\.venv\Scripts\python.exe bots\public_bot.py

# Terminal 3: Bot privado (escucha la cola)
.\.venv\Scripts\python.exe bots\private_bot.py
```

El bot público envía mensajes a Redis cuando detecta riesgo; bot privado ejecuta acciones.

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

---

## 🔄 Cambios en esta versión (v1.3.0)

### 🔧 Fixes críticos:
1. **Instancias múltiples de bots** → Ahora usa file-based locking (`.private_bot.lock`, `.public_bot.lock`)
   - Previene que dos instancias del mismo bot corra simultáneamente
   - Error claro si intentas iniciar una segunda instancia

2. **Handlers síncronos en public_bot** → Ahora son async
   - `ingest()` convertido a `async def ingest()` 
   - `member_change()` convertido a `async def member_change()`
   - Evita bloqueos del event loop

3. **Deduplicación de mensajes** → Redis-backed mensaje dedup
   - Ventana de 2 segundos para mensajes duplicados
   - Ventana de 3 segundos para eventos de join
   - Usa hashing MD5 para detección rápida

4. **Launcher profesional** → `start_bots.py`
   - Supervisión automática de botses
   - Restart automático en crashes
   - Logs centralizados y monitoring

---

## 🐛 Troubleshooting

### Bot lanza error "Another instance is already running"

**Causa:** Hay un `.lock` file de una sesión anterior que no se limpió.

**Solución:**
```powershell
# Windows - listar archivos lock
Get-ChildItem -Hidden -Filter "*.lock" C:\workspace\telegram_antifraud\

# Eliminar archivos lock manualmente
Remove-Item C:\workspace\telegram_antifraud\.private_bot.lock -Force
Remove-Item C:\workspace\telegram_antifraud\.public_bot.lock -Force

# Linux/Mac
rm -f .private_bot.lock .public_bot.lock
```

### Bot responde dobles a cada comando

**Causa:** La versión anterior había corriendo múltiples instancias.

**Solución:**
```powershell
# Detener todos los procesos python
Get-Process python | Stop-Process -Force

# Limpiar locks
Remove-Item .*.lock -Force -ErrorAction SilentlyContinue

# Reiniciar con launcher
.\.venv\Scripts\python.exe start_bots.py --verbose
```

### Bot no se inicio / "database is locked"

**Causa:** Session file de Pyrogram está bloqueado.

**Solución:**
```powershell
# El fix (in_memory=True) debería prevenirlo
# Pero si aun ocurre en sesiones antiguas:
Remove-Item sessions/private_bot.* -Force -ErrorAction SilentlyContinue
Remove-Item sessions/public_bot.* -Force -ErrorAction SilentlyContinue
```

### Redis no está disponible

**Causa:** Redis es opcional pero recomendado para cola de acciones.

**Nota:** El bot seguirá funcionando sin Redis, pero la cola de acciones será deshabilitada.

```powershell
# Opcionalmente iniciar Redis
docker run -d -p 6379:6379 redis:7-alpine
```

---

## 📊 Monitoreo en producción

```bash
# Terminal 1: Ver logs del bot privado
tail -f logs_private_bot.txt    # o logs/private_bot.log

# Terminal 2: Ver logs del bot público  
tail -f logs_public_bot.txt     # o logs/public_bot.log

# Terminal 3: Health checks periódicos
while true; do
  sleep 60
  curl http://localhost:8000/health 2>/dev/null || echo "Bot unhealthy"
done
```

---

## 📝 Admin Commands (private bot)

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/start` | Menú principal | `/start` |
| `/whoami` | Muestra tu ID y estado admin | `/whoami` |
| `/ban <id> [razón]` | Banea usuario | `/ban 123456789 spam` |
| `/unban <id>` | Desbanea usuario | `/unban 123456789` |
| `/strike <id> [razón]` | Añade strike | `/strike 123456789 warning` |
| `/forgive <id>` | Quita strike | `/forgive 123456789` |
| `/user <id>` | Info del usuario | `/user 123456789` |
| `/risk <id>` | Risk assessment | `/risk 123456789` |
| `/stats` | Estadísticas del sistema | `/stats` |
| `/listbans` | Lista usuarios baneados | `/listbans` |
| `/test` | Sistema tests | `/test` |
| `/ping` | Ping del bot | `/ping` |
