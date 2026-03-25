# Telegram Anti-Fraud System

**Production-ready reference implementation** for detecting and mitigating malicious operators in Telegram (spam, raids, scams, multi-accounting).

[![GitHub CI](https://github.com/DonGerte/telegram_antifraud/actions/workflows/ci.yml/badge.svg)](https://github.com/DonGerte/telegram_antifraud/actions) ![GitHub Release](https://img.shields.io/github/v/release/DonGerte/telegram_antifraud?style=flat&label=Release) [![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Status:** ✅ **PRODUCTION READY** – Complete antifraud system with risk scoring, strikes, memory, and admin controls  
**License:** MIT – See [LICENSE](LICENSE), [COPYRIGHT.md](COPYRIGHT.md), and [COPYING](COPYING)  
**Last Updated:** March 3, 2026

---

## 🎯 System Overview

This is a **complete, containerized anti-fraud solution** with advanced risk assessment and automated moderation:

### Core Detection Engine
- **Risk Assessment**: Multi-factor risk scoring (SAFE/SUSPICIOUS/DANGEROUS/BANNED levels)
- **Strike System**: Progressive discipline (1-3 strikes to ban)
- **User Memory**: Persistent behavior tracking with JSON storage
- **Behavior Fingerprinting**: Multi-account detection via pattern analysis
- **Message Analysis**: Content-based risk evaluation
- **Raid Detection**: Coordinated attack pattern recognition

### Moderation Infrastructure
- **Admin Bot**: Comprehensive command interface for user management
- **Automated Actions**: Risk-based automatic moderation
- **Memory Persistence**: User history and behavior tracking
- **Test Mode**: Validation without Telegram connection
- **Comprehensive Testing**: Full test suite for all components

### Production Readiness
- ✅ Docker Compose containerization (Redis + bots)
- ✅ JSON-based user database with metadata
- ✅ Automated test suite (comprehensive validation)
- ✅ Admin command interface
- ✅ Risk assessment engine
- ✅ Strike and ban management
- ✅ Memory and fingerprinting systems

---

## 📁 Project Structure

```
telegram_antifraud/
├── bots/
│   ├── public_bot.py          # Main bot with antifraud integration
│   ├── private_bot.py         # Admin bot with management commands
│   └── userbot.py             # Userbot for investigation
├── engine/
│   ├── risk_assessment.py     # Risk level evaluation engine
│   ├── scoring.py             # Message and behavior scoring
│   ├── clusters.py            # Multi-account detection
│   ├── honeypot.py            # Spam pattern matching
│   ├── raid.py                # Raid detection and containment
│   ├── signals.py             # Signal definitions
│   └── logger.py              # Event logging
├── services/
│   ├── memory.py              # User data persistence
│   ├── strike_manager.py      # Strike progression system
│   └── ban_manager.py         # Ban management and fingerprinting
├── data/
│   └── store.json             # User database
├── examples/
│   ├── logging.py             # Logging examples
│   └── metrics.py             # Metrics collection
├── tests.py                   # Comprehensive test suite
├── docker-compose.yml         # Multi-service setup
├── requirements.txt           # Python dependencies
├── config.py                  # Configuration settings
└── README.md                  # This file
```

---

## 🚀 Inicio Rápido

### 1. Obtener Tokens de Bot
1. Ve a [@BotFather](https://t.me/BotFather) en Telegram
2. Crea dos bots:
   - `/newbot` → Bot público (para monitoreo de grupos)
   - `/newbot` → Bot privado (para comandos admin)
3. Copia los tokens que te da BotFather

### 2. Configurar el Sistema
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar setup interactivo
python run.py
```

El script de setup te guiará para:
- ✅ Verificar dependencias
- ✅ Crear archivo `.env` con tus tokens
- ✅ Verificar Redis
- ✅ Ejecutar tests
- ✅ Iniciar los bots

### 3. Archivo .env
Crea un archivo `.env` en la raíz del proyecto:
```env
PUBLIC_BOT_TOKEN=tu_token_del_bot_publico
PRIVATE_BOT_TOKEN=tu_token_del_bot_privado
REDIS_URL=redis://localhost:6379/0
```

### 4. Iniciar Redis
```bash
# Instalar Redis (Windows con Chocolatey)
choco install redis-64

# O usar Docker
docker run -d -p 6379:6379 redis:7-alpine

# Iniciar Redis
redis-server
```

### 5. Ejecutar los Bots
```bash
# Opción A: Usar el script interactivo
python run.py
# Selecciona opción 3 para ejecutar ambos bots

# Opción B: Manualmente en terminales separadas
# Terminal 1: Bot público (monitoreo)
python bots/public_bot.py

# Terminal 2: Bot privado (admin)
python bots/private_bot.py
```

### 6. Probar el Bot
1. **Bot Público**: Envia `/start` en chat privado con el bot público
2. **Bot Admin**: Envia `/start` en chat privado con el bot privado
3. **En Grupo**: Agrega el bot público a un grupo como administrador

### 7. Comandos Disponibles

#### Bot Público (Monitoreo)
- `/start` - Información del bot
- `/help` - Ayuda
- `/status` - Estado del sistema

#### Bot Privado (Admin)
- `/start` - Lista de comandos
- `/stats` - Estadísticas del sistema
- `/user <id>` - Información de usuario
- `/ban <id> [razón]` - Banear usuario
- `/unban <id>` - Desbanear usuario
- `/strike <id> [razón]` - Agregar strike
- `/forgive <id>` - Quitar strike
- `/risk <id>` - Evaluar riesgo
- `/containment <chat_id> <modo>` - Modo contención
- `/whitelist <id>` - Agregar a whitelist
- `/blacklist <id>` - Agregar a blacklist
- `/test` - Ejecutar tests

### 8. Verificar Funcionamiento
```bash
# Ejecutar tests
python tests.py

# Modo test (sin Telegram)
python bots/public_bot.py --test-mode
python bots/private_bot.py --test-mode
```
python bots/private_bot.py --test-mode

# Run full test suite
python tests.py
```

---

## 🎯 Core Features

### Risk Assessment Engine
- **Multi-level Risk**: SAFE, SUSPICIOUS, DANGEROUS, BANNED
- **Factor-based Scoring**: Combines message content, user history, and behavior patterns
- **Real-time Evaluation**: Assess risk on every message and user action

### Strike System
- **Progressive Discipline**: 1st strike (warning), 2nd strike (restriction), 3rd strike (ban)
- **Reason Tracking**: Detailed strike history with timestamps
- **Flexible Management**: Add/remove strikes via admin commands

### User Memory System
- **Persistent Storage**: JSON-based user database
- **Behavior Tracking**: Message history, strikes, bans, timestamps
- **Metadata Management**: First seen, last seen, tags, whitelist/blacklist

### Admin Command Interface
Comprehensive bot management via private chat:

```
/start - Show available commands
/stats - System statistics
/user <id> - User information and risk assessment
/ban <id> [reason] - Ban user
/unban <id> - Unban user
/strike <id> [reason] - Add strike to user
/forgive <id> - Remove strike from user
/risk <id> - Assess user risk
/containment <chat_id> <mode> - Set containment mode
/whitelist <id> - Add to whitelist
/blacklist <id> - Add to blacklist
/test - Run system tests
```

### Automated Moderation
- **Risk-based Actions**: Automatic moderation based on risk levels
- **Strike Progression**: Automatic strikes for suspicious behavior
- **Ban Automation**: Automatic bans after 3 strikes
- **Containment Modes**: Slow mode, bunker mode for raid protection

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
python tests.py
```

Tests cover:
- ✅ Memory service functionality
- ✅ Strike manager operations
- ✅ Ban manager and fingerprinting
- ✅ Risk assessment engine
- ✅ Scoring algorithms
- ✅ Full system integration

---

## 🔧 Configuration

### Bot Configuration (`config.py`)
```python
# Telegram Bot Tokens
PUBLIC_BOT_TOKEN = "your_public_bot_token_here"
PRIVATE_BOT_TOKEN = "your_private_bot_token_here"

# Redis Configuration
REDIS_URL = "redis://localhost:6379/0"

# Risk Assessment Thresholds
SAFE_THRESHOLD = 0.3
SUSPICIOUS_THRESHOLD = 0.6
DANGEROUS_THRESHOLD = 0.8

# Strike Configuration
MAX_STRIKES_BEFORE_BAN = 3

# Memory Configuration
STORE_FILE = "data/store.json"
```

### User Database (`data/store.json`)
```json
{
  "users": {
    "12345": {
      "message_count": 10,
      "strikes": 1,
      "banned": false,
      "first_seen": "2024-01-01T10:00:00Z",
      "last_seen": "2024-01-02T15:30:00Z",
      "tags": ["suspicious"],
      "strike_history": [
        {"reason": "spam", "timestamp": "2024-01-02T14:00:00Z"}
      ]
    }
  },
  "metadata": {
    "last_updated": "2024-01-02T15:30:00Z",
    "version": "1.0"
  }
}
```

---

## 🚀 Deployment Options

### Docker Compose
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  public-bot:
    build: .
    command: python bots/public_bot.py
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  private-bot:
    build: .
    command: python bots/private_bot.py
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

### Production Deployment
1. **Set up Redis cluster** for high availability
2. **Configure monitoring** with Prometheus/Grafana
3. **Set up backups** for user database
4. **Configure logging** aggregation
5. **Set up health checks** and alerting

---

## 📊 Monitoring & Metrics

### System Statistics
- Total users tracked
- Active bans and strikes
- Risk distribution
- Message processing rate
- System uptime and performance

### Admin Dashboard
Access via private bot commands to monitor:
- User statistics
- Risk assessments
- Strike distributions
- System health

---

## 🔒 Security & Compliance

### Data Protection
- User data stored locally in JSON format
- No external data sharing
- Configurable data retention
- GDPR-compliant data handling

### Access Control
- Private admin bot for management commands
- Token-based authentication
- Command-level permissions

### Audit Trail
- Comprehensive logging of all actions
- Strike and ban history
- Admin command usage tracking

---

## 🛠️ Development

### Adding New Features
1. **Risk Factors**: Extend `engine/risk_assessment.py`
2. **Admin Commands**: Add to `bots/private_bot.py`
3. **Memory Fields**: Update `services/memory.py`
4. **Tests**: Add to `tests.py`

### Code Quality
- Comprehensive test coverage
- Type hints and documentation
- Modular architecture
- Error handling and logging

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

**Built with ❤️ for safer Telegram communities**
├── engine/
│   ├── scoring.py             # User risk scoring with decay
│   ├── clusters.py            # Multi-account network detection (BFS)
│   ├── honeypot.py            # Spam template matching (Levenshtein)
│   ├── raid.py                # Join spike detection + containment modes
│   ├── signals.py             # Signal definitions (link, honeypot, velocity, etc.)
│   ├── rules.py               # Decision engine (AND/OR, priorities)
│   ├── worker.py              # Main processing pipeline
│   ├── shadow_mod.py          # Silent moderation (throttle, mute, suppress)
│   └── logger.py              # Structured JSON event logging
├── db/
│   └── models.py              # SQLAlchemy ORM (6 models, migrations ready)
├── api/
│   └── dashboard.py           # FastAPI REST API (13 endpoints)
├── tools/
│   ├── traffic_simulator.py   # Synthetic attack generation (6 modes)
│   ├── userbot_opsec.py       # Session rotation, proxy management
│   └── metrics.py             # Prometheus integration (docs)
├── docs/
│   ├── MODERATION_POLICY.md   # Behavior classification & moderator roles
│   ├── TOS_CHECKLIST.md       # GDPR, CCPA, Telegram compliance matrix
│   ├── PRIVACY_POLICY.md      # User data practices & rights
│   ├── SECURITY_POLICY.md     # Incident response, vulnerability disclosure
│   ├── OPERATIONS_MANUAL.md   # Deployment, monitoring, troubleshooting
│   └── SCALABILITY.md         # Redis Cluster, Kafka, multi-worker setups
├── tests/
│   └── test_advanced.py       # 14 comprehensive pytest tests
├── docker-compose.yml         # Full stack: Redis + 3 bots + dashboard
├── Dockerfile                 # Python 3.11 container image
├── config.py                  # Centralized configuration
├── requirements.txt           # Pinned dependencies (FastAPI, SQLAlchemy, Pyrogram)
├── .env.example              # Template for credentials
├── rules.json                # 5 example rules (priorities, conditions)
├── demo.py                   # 5-demo showcase of all subsystems
└── README.md                 # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** or **Docker**
- **Redis 6.0+** (bundled in docker-compose)
- **PostgreSQL 13+** (optional, for persistence)
- **Telegram bot tokens** (create via [@BotFather](https://t.me/BotFather))

### Installation

1. **Clone & setup environment:**
   ```bash
   git clone https://github.com/your-org/telegram_antifraud
   cd telegram_antifraud
   cp .env.example .env
   # Edit .env with your Telegram tokens and Redis URL
   nano .env
   ```

2. **Option A: Docker Compose (Recommended)**
   ```bash

### Webhook mode (Full production)

The project now includes a webhook endpoint and a worker pipeline:

- API: `bots/webhook.py` (FastAPI, accepts Telegram updates at `/webhook`)
- Worker: `engine/worker.py` (consumes `data_bus`, processes rules, pushes actions to `action_bus`)
- Helper script: `scripts/setup_webhook.sh` to set Telegram webhook

To use:

1. Set `WEBHOOK_URL` and `WEBHOOK_SECRET_TOKEN` in `.env`.
2. Start compose:
   ```bash
   docker compose up -d
   ```
3. Configure webhook:
   ```bash
   ./scripts/setup_webhook.sh
   ```
4. Validate service:
   ```bash
   curl http://localhost:8000/healthz
   ```

------

2. **Option A: Docker Compose (Recommended)**
   ```bash
   docker-compose up -d
   # Services: public_bot, worker, private_bot, redis all running
   docker-compose logs -f worker  # Monitor processing
   ```

3. **Option B: Local Python**
   ```bash
   pip install -r requirements.txt
   # Terminal 1: python bots/public_bot.py
   # Terminal 2: python engine/worker.py
   # Terminal 3: python bots/private_bot.py

---

## ☸️ Kubernetes Deployment (Large Groups)

For high‑traffic groups the recommended platform is Kubernetes. A simple cluster offers
high availability, auto‑scaling and the ability to handle tens of thousands of messages
per minute. The `k8s/` directory contains example manifests that match this repository's
architecture.

1. **Build & publish** a container image to a registry, e.g. `ghcr.io/<you>/telegram_antifraud:latest`.
2. **Create secrets** for the database and Telegram token:
   ```sh
   kubectl create secret generic telegram-secret --from-literal=token="$TELEGRAM_TOKEN"
   kubectl create secret generic antifraud-db-secret --from-literal=password="supersecret"
   ```
3. **Apply infrastructure manifests** (adjust storage classes and resource sizes):
   ```sh
   kubectl apply -f k8s/redis-statefulset.yaml
   kubectl apply -f k8s/postgres-deployment.yaml
   kubectl apply -f k8s/webhook-deployment.yaml
   kubectl apply -f k8s/worker-deployment.yaml
   kubectl apply -f k8s/ingress.yaml
   kubectl apply -f k8s/hpa.yaml
   ```
4. **Configure TLS & DNS**: ensure `cert-manager` is installed and `yourdomain.example.com` points
to the ingress controller. Webhook endpoint should be `https://yourdomain.example.com/webhook`.
5. **Autoscaling**: the HPA uses CPU and a custom Prometheus metric (`redis_queue_length`) to

---

## 🔧 Utilities

* `tools/backup.py` – scheduleable Postgres/Redis backup helper (see docs/OPERATIONS_MANUAL.md).
* `tools/sdk.py` – simple Python client for the REST API.
* `tools/load_test.py` – generate traffic against the webhook endpoint for benchmarking.

These are useful when automating maintenance, integrating with other systems, or
validating performance under load.

---

grow/shrink the worker set automatically.

> With this setup the system can scale horizontally by simply increasing the
> Replica count or allowing the HPA to adjust based on load. Redis and Postgres are
> the only stateful services and can be backed by managed offerings for production.

---

Hecho por hasbulla
   # Terminal 4: uvicorn api.dashboard:app --reload
   ```

### Verify Installation
```bash
# Add bot to Telegram chat
# Send test message in chat (bot should process it)

# Check dashboard
open http://localhost:8000/docs  # Swagger UI with all endpoints

# Run test suite
pytest tests/test_advanced.py -v  # Should see 14/14 passing

# Simulate spam attack
python tools/traffic_simulator.py --attack spam --chat <YOUR_CHAT_ID>
```

---

## 🛠️ Configuration

### Core Configuration (`config.py`)
```python
# Telegram tokens (from .env)
TELEGRAM_TOKEN_PUBLIC = "1234567:ABC..."
TELEGRAM_TOKEN_PRIVATE = "7654321:XYZ..."

# Redis
REDIS_URL = "redis://localhost:6379/0"

# Scoring thresholds
VELOCITY_THRESHOLD = 40      # msg/hour to flag
RAID_THRESHOLD = 15          # joins in 5 min to trigger raid mode
SCORE_BAN_THRESHOLD = 120    # kick user if score > 120

# Database (optional)
DATABASE_URL = "postgresql://user:pass@localhost/antifraud"
```

### Rules Configuration (`rules.json`)
```json
[
  {
    "name": "high_score_kick",
    "priority": 1,
    "conditions": {
      "type": "AND",
      "items": [{"type": "score_gt", "value": 100}]
    },
    "actions": ["kick"],
    "enabled": true
  },
  {
    "name": "honeypot_immediate_kick",
    "priority": 2,
    "conditions": {
      "type": "AND",
      "items": [
        {"type": "has_signal", "value": "honeypot"},
        {"type": "velocity_gt", "value": 20}
      ]
    },
    "actions": ["kick"],
    "enabled": true
  }
]
```

---

## 🎯 Core Features

### 1. Detection Engine
| Signal | Description | Implementation |
|--------|-------------|-----------------|
| **Velocity** | High message rate | defaultdict + time windows |
| **Repetition** | Duplicate messages | MD5 hash matching |
| **Honeypot** | Known spam templates | Levenshtein distance (< 0.3) |
| **Raid** | Coordinated joins | Join spike detection + clustering |
| **Links** | Suspicious URLs | Keyword/tld blacklist |
| **Cluster** | Multi-account networks | BFS graph traversal |

### 2. Moderation Actions
```python
Actions: ["kick", "mute", "restrict", "raid_alert", "raid_bunker", "containment_off"]

# Examples
kick(chat_id, user_id, reason="spam detected")
restrict(chat_id, user_id, can_send_messages=False)  # Soft ban
```

### 3. FastAPI Dashboard
**13 REST endpoints for moderators:**
- `GET /api/users` – List users (filtered by score/status)
- `GET /api/users/{uid}` – User details + signal history
- `POST /api/users/{uid}/action` – Manual moderator action
- `GET/POST/PUT/DELETE /api/rules` – Rule CRUD
- `GET /api/alerts` – Recent actions
- `GET /api/audit` – Audit trail
- `GET /api/stats` – System dashboard

**Auto-generated docs:** http://localhost:8000/docs (Swagger UI)

### 4. Database Schema
**6 SQLAlchemy ORM models:**
- **User**: telegram_id, score, status, last_seen
- **Signal**: signal_type, value, chat_id, raw_text, timestamp
- **ModAction**: audit records of all kicks/mutes/restricts
- **Rule**: versioned rule storage with created_by audit
- **AuditLog**: comprehensive action log (who did what, when)
- **Session factory**: async-ready for production

**Migration-ready:** Use Alembic for schema updates

### 5. Compliance & Governance
- ✅ **GDPR**: Data minimization, encryption, right to deletion
- ✅ **CCPA**: Opt-out, data disclosure, non-discrimination
- ✅ **Telegram ToS**: Rate limit compliance, API usage policy
- ✅ **Privacy**: Structured logging, user consent mechanisms
- ✅ **Security**: Vulnerability disclosure, incident response

**Policy documents included:**
- `MODERATION_POLICY.md` – Behavior classification, moderator roles, escalation
- `TOS_CHECKLIST.md` – GDPR/CCPA/Telegram compliance matrix
- `PRIVACY_POLICY.md` – Data collection, retention, user rights
- `SECURITY_POLICY.md` – Incident response, vulnerability reporting
- `OPERATIONS_MANUAL.md` – Deployment, monitoring, troubleshooting

---

## 📊 Event Flow

```
Public Bot                Redis Queue                 Worker                  Database
(Telegram API)            (data_bus)                  (Rules Engine)          (PostgreSQL)
   │                          │                           │                         │
   ├─ User sends message ──→ Data Bus              Process signal ───→ Audit Log
   │  - user_id, text         - store ~100 events     - calc score       - Store signals
   │  - timestamp             - 1sec TTL              - check rules       - Store actions
   │  - chat_id                                       - trigger action
   │                                                      │
   ├─ User joins chat ────→ Data Bus                    │
   │  - user_id, join_time    - store joins            │
   │                          - detect raid            │
   │                              │
   │                         Action Bus (action_bus)◄──┘
   │                         - kick: user 123
   │                         - mute: user 456
   │                         - raid_bunker: chat_id
   │                              │
   └─ Private Bot (Action Handler)
      - Execute kick/mute/restrict
      - Log result to audit_bus
      - Send moderator notification
```

---

## 🧪 Testing & Validation

### Run Test Suite
```bash
pytest tests/test_advanced.py -v

# Expected output:
# test_scoring.py::test_velocity_tracking ✓
# test_scoring.py::test_repetition_detection ✓
# test_honeypot.py::test_levenshtein_similarity ✓
# test_rules.py::test_rule_engine_and_or ✓
# test_raid.py::test_raid_detection ✓
# ... (14 total)
# ======== 14 passed in 2.34s ========
```

### Demo All Features
```bash
python demo.py

# Showcases:
# 1. Velocity detection (high-rate messages)
# 2. Repetition detection (duplicate messages)
# 3. Honeypot similarity (spam template matching)
# 4. Raid detection (coordinated joins)
# 5. Rule engine evaluation (complex conditions)

### Simulate Traffic
```bash
python tools/traffic_simulator.py --attack spam --chat <YOUR_CHAT_ID>
python tools/traffic_simulator.py --attack raid --chat <YOUR_CHAT_ID>
python tools/traffic_simulator.py --attack all --chat <YOUR_CHAT_ID>
```

---

## 📦 Production Deployment

### Docker Compose (Single Host)
```bash
# Start all services
docker-compose up -d

# Verify
docker-compose ps
# redis:6379 ✓ | public_bot ✓ | worker ✓ | private_bot ✓

# Monitor
docker-compose logs -f worker
```

### Kubernetes (Advanced Scaling)
```bash
# Deploy multi-replica worker pool
kubectl apply -f k8s/antifraud-deployment.yaml

# Multi-worker + Redis Sentinel HA
# See docs/SCALABILITY.md for Kafka setup
```

### Environment Variables (`.env`)
```bash
# Telegram
TELEGRAM_TOKEN_PUBLIC=your_public_bot_token
TELEGRAM_TOKEN_PRIVATE=your_private_bot_token

# Redis (production: use SSL)
REDIS_URL=rediss://password@redis-cluster:6379

# PostgreSQL (production: use SSL)
DATABASE_URL=postgresql://user:pwd@db-host/antifraud?sslmode=require

# Configuration
RAID_THRESHOLD=15           # joins triggering raid
VELOCITY_THRESHOLD=40       # msg/hour to flag
RULES_FILE=rules.json
```

---

## 🔒 Security & Compliance

### GDPR Compliance ✅
- **Data minimization**: Only collect user_id, score, signals (not full messages)
- **Retention**: Auto-delete user data after 90 days inactivity
- **User rights**: `/data_disclosure`, `/delete_my_data`, `/opt_out` commands
- **Processing basis**: Legitimate interest (spam/fraud prevention)

### CCPA Compliance ✅
- **Consumer rights**: Know, Delete, Opt-Out, Non-Discrimination
- **Data broker clause**: No third-party data sales
- **Disclosure**: Privacy policy available at `/privacy`

### Telegram ToS Compliance ✅
- Rate limits respected (100 msg/min per chat)
- API usage limited to moderation (kick, mute, restrict)
- Private bot has minimal permissions
- No intercepting private messages

### Security Features ✅
- Secrets stored in `.env` (excluded from git)
- TLS 1.3 for API communication
- Immutable audit logs (append-only, tamper-proof)
- Structured JSON logging for forensics
- Incident response playbook included

**See `docs/` for full policies:**
- `SECURITY_POLICY.md` – Vulnerability disclosure, incident response
- `PRIVACY_POLICY.md` – User data practices & rights
- `MODERATION_POLICY.md` – Behavior classification & appeals
- `TOS_CHECKLIST.md` – Compliance matrix (GDPR, CCPA, Telegram)

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `MODERATION_POLICY.md` | 5-tier behavior classification, moderator roles, escalation procedures |
| `TOS_CHECKLIST.md` | GDPR/CCPA/Telegram compliance mapping + implementation status |
| `PRIVACY_POLICY.md` | Data collection, retention, user rights, FAQs |
| `SECURITY_POLICY.md` | Incident response, vulnerability reporting, audit schedule |
| `OPERATIONS_MANUAL.md` | Deployment, monitoring, troubleshooting, incident playbooks |
| `SCALABILITY.md` | Redis Cluster, Kafka setup, multi-worker deployment, monitoring |

---

## 🎯 Architecture Decisions

### Why Redis for Event Queue?
- **Sub-millisecond latency** for message processing
- **Persistence** via RDB/AOF for recovery
- **Horizontal scaling** with Redis Cluster (millions of events/day)
- **Developer-friendly** Pub/Sub + List operations

### Why PostgreSQL for Audit?
- **ACID compliance** for data integrity
- **Queryable JSON** for flexible logging
- **Indexes** on audit_log for fast forensics
- **Replication** for high availability

### Why SQLAlchemy ORM?
- **Schema safety** with migrations (Alembic)
- **Type safety** with Pydantic integration
- **Relationship management** (User ↔ Signal ↔ Action)
- **Production-ready** connection pooling

### Why FastAPI for Dashboard?
- **Auto-generated docs** (Swagger/ReDoc)
- **Type validation** via Pydantic
- **Async support** for 1000s of concurrent moderators
- **CORS-ready** for web frontend integration

---

## 📊 Scaling Strategy

| Traffic Volume | Architecture | Details |
|---|---|---|
| < 1M msg/day | Redis single instance | This deployment |
| 1M – 10M msg/day | Redis Cluster (3+ nodes) | Horizontal sharding |
| > 10M msg/day | Redis + Kafka + multi-worker | Event sourcing, replay |

**See `docs/SCALABILITY.md` for:**
- Docker Compose Redis Cluster setup (3-node)
- Kafka topic configuration (partition strategy)
- Multi-worker deployment (replicas=4+)
- Monitoring with Prometheus/Grafana
- PostgreSQL read replicas for queries

---

## 🐛 Troubleshooting

### Bot not responding
```bash
# Check public_bot logs
docker-compose logs public_bot | tail -20

# Verify Telegram token
curl https://api.telegram.org/bot${TOKEN}/getMe | jq .ok

# Restart bot
docker-compose restart public_bot
```

### Workers not processing messages
```bash
# Check queue backlog
redis-cli LLEN data_bus  # Should be small (< 1000)

# Check worker logs
docker-compose logs worker | grep ERROR

# Verify database connection
docker-compose logs worker | grep "connection"

# Restart worker
docker-compose restart worker
```

### High memory in Redis
```bash
redis-cli INFO memory
# If > 1 GB, check:
# - Are signals being purged? (90-day retention)
# - Is worker stuck processing old events?
# - Set EXPIRE on queues: redis-cli EXPIRE data_bus 86400
```

**For complete troubleshooting:** See `docs/OPERATIONS_MANUAL.md`

---

## 💻 Development

### Install Dev Dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock  # testing
pip install black ruff mypy                      # linting
```

### Run Tests
```bash
pytest tests/ -v                    # All tests
pytest tests/test_advanced.py::test_rule_engine_and_or -v  # Single test
pytest --cov=engine tests/          # Coverage report
```

### Code Quality
```bash
black engine/ bots/ api/ tools/     # Format
ruff check engine/ bots/ api/       # Lint
mypy engine/ --strict               # Type check
```

### Debug Locally
```bash
# Run with local Redis (no Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Set environment
export TELEGRAM_TOKEN_PUBLIC=...
export REDIS_URL=redis://localhost:6379

# Run components
python bots/public_bot.py  # Terminal 1
python engine/worker.py    # Terminal 2
python bots/private_bot.py # Terminal 3
```

---

## 📈 Metrics & Monitoring

### Key Metrics
```
worker_messages_processed         # Total messages analyzed
worker_actions_taken             # Total moderation actions
worker_error_count               # Processing failures
worker_latency_ms                # Time per message (p50, p99)
active_users_risk_score_gt_50    # High-risk user count
raids_detected_today             # Raid events
false_positive_rate              # % of kicks that were wrong
```

### Prometheus Integration
```bash
# Enable metrics in worker.py
# Scrape endpoint: /metrics

docker-compose -f docker-compose.monitoring.yml up -d
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

---

## 🔄 Workflow

### For Moderators
1. **Dashboard** → Review alerts in real-time
2. **User detail** → Inspect score, signal history, appeals
3. **Manual action** → Kick/mute/restrict if needed
4. **Appeal review** → Check user's `/appeal` request
5. **Audit trail** → Verify all actions logged

### For Engineers
1. **Rules update** → Edit `rules.json`, test with simulator
2. **Signal addition** → Extend `engine/signals.py`
3. **Scoring tweak** → Adjust weights in `engine/scoring.py`
4. **Deploy** → Merge → CI/CD → production docker-compose restart

### For Security/Compliance
1. **Policy review** → Quarterly check of `MODERATION_POLICY.md`
2. **Incident audit** → Review `audit_log` table for anomalies
3. **Compliance scan** → Verify GDPR/CCPA checklist
4. **Penetration test** → Annual security audit

---

## 🚨 Incident Response

**P1 Emergency (data loss, all bots down):**
1. Page on-call engineer immediately
2. Check `docker-compose ps` for failed services
3. Review logs: `docker-compose logs --since 10m` 
4. Restore from backup: `psql $DB < backup.sql`
5. Restart: `docker-compose restart`

**P2 High (moderators can't kick, > 5% errors):**
1. Check worker logs for exceptions
2. Verify database connection
3. Restart worker: `docker-compose restart worker`
4. If persists, escalate to DBA

**See `docs/OPERATIONS_MANUAL.md` for full incident playbook**

---

## 📝 License & Legal

This code is provided as-is for reference. When deploying in production:

- ✅ Review `docs/SECURITY_POLICY.md` for vulnerability reporting
- ✅ Publish `docs/PRIVACY_POLICY.md` to users
- ✅ Follow `docs/MODERATION_POLICY.md` for appeals
- ✅ Validate `docs/TOS_CHECKLIST.md` compliance with your legal team
- ✅ Archive `docs/OPERATIONS_MANUAL.md` for future operators

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch (`feature/your-idea`)
3. Add tests (must pass: `pytest`)
4. Submit pull request with description
5. Address security/compliance review

---

## 📞 Support

**Documentation:** See `/docs` folder for detailed guides  
**Issues:** Report via GitHub Issues  
**Security:** Email security@example.com (see `SECURITY_POLICY.md`)  
**Questions:** Create Discussion in GitHub

---

## 🎓 Roadmap

- ✅ Phase 1-5: Core detection (velocity, repetition, honeypot, raid, clustering)
- ✅ Phase 6-9: Advanced features (rules, shadow_mod, OPSEC, logging)
- ✅ Phase 10-12: Persistence (database, dashboard, API)
- ✅ Phase 13-16: Production infrastructure (simulator, scaling, docs)
- ⏳ Phase 17: Grafana dashboards (monitoring)
- ⏳ Phase 18: A/B testing framework (rule variants)
- ⏳ Phase 19: Web UI for moderators (React/Next.js frontend)

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact & Support

- **Email:** hasbullita007@gmail.com
- **GitHub Issues:** [Report bugs or request features](https://github.com/DonGerte/telegram_antifraud/issues)
- **GitHub Discussions:** [Ask questions or share ideas](https://github.com/DonGerte/telegram_antifraud/discussions)
- **Support Guide:** [See SUPPORT.md](SUPPORT.md)
- **Contributing Guide:** [See CONTRIBUTING.md](CONTRIBUTING.md)

For security vulnerabilities, please refer to [SECURITY.md](docs/SECURITY_POLICY.md).

---

**Hecho por hasbulla con ❤️ para una moderación segura y transparente**  
**Última actualización:** 3 de marzo de 2026
