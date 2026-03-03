# Operations Manual

**For:** System Administrators, Moderators, Infrastructure Engineers  
**Last Updated:** March 3, 2026  
**Status:** Production Ready

---

## Table of Contents
1. [Deployment](#1-deployment)
2. [Monitoring](#2-monitoring)
3. [Maintenance](#3-maintenance)
4. [Troubleshooting](#4-troubleshooting)
5. [Incident Response](#5-incident-response)
6. [Escalation Contacts](#6-escalation-contacts)

---

## 1. Deployment

### 1.1 Prerequisites
Before deploying the system, ensure:

- [ ] Linux server (Ubuntu 20.04+ or CentOS 8+)
- [ ] Docker and Docker Compose installed
- [ ] PostgreSQL 13+ (cloud-hosted or on-premise)
- [ ] Redis 6.0+ (standalone or cluster)
- [ ] 4+ GB RAM, 10 GB disk space
- [ ] Telegram bot tokens (both public and private)

### 1.2 Pre-Deployment Checklist

```bash
# 1. Clone repository
git clone https://github.com/your-org/telegram_antifraud
cd telegram_antifraud

# 2. Set up environment
cp .env.example .env
# Edit .env with actual values:
# - TELEGRAM_TOKEN_PUBLIC=<public_bot_token>
# - TELEGRAM_TOKEN_PRIVATE=<private_bot_token>
# - REDIS_URL=redis://localhost:6379
# - DATABASE_URL=postgresql://user:pass@host/db
nano .env

# 3. Verify credentials
python -c "from config import *; print(f'Tokens loaded: {bool(TELEGRAM_TOKEN_PUBLIC)} + {bool(TELEGRAM_TOKEN_PRIVATE)}')"

# 4. Test database connection
python -c "from db.models import engine; engine.connect(); print('✅ DB OK')"

# 5. Test Redis connection
python -c "import redis; r=redis.from_url('${REDIS_URL}'); r.ping(); print('✅ Redis OK')"
```

### 1.3 Starting the System

#### Option A: Docker Compose (Recommended)
```bash
# Single command startup
docker-compose up -d

# Verify all services running
docker-compose ps
# Should show: public_bot, worker, private_bot, redis - all "Up"

# View logs
docker-compose logs -f worker
```

#### Option B: Manual Python (Development)
```bash
# Terminal 1: Public bot
python bots/public_bot.py

# Terminal 2: Worker
python engine/worker.py

# Terminal 3: Private bot
python bots/private_bot.py

# Terminal 4: Dashboard API
uvicorn api.dashboard:app --host 0.0.0.0 --port 8000 --reload
```

### 1.4 Deployment Verification

```bash
# Check all components healthy
curl -s http://localhost:8000/api/health || echo "API unreachable"

# Verify public bot is in chat (check Telegram)
# Message should appear in chat moderator group

# Test a moderation action (simulate spam)
python tools/traffic_simulator.py --attack spam --chat <YOUR_CHAT_ID>

# Check dashboard
open http://localhost:8000/docs  # Swagger UI with all endpoints
```

### 1.5 Production Deployment (Cloud)

#### On AWS EC2:
```bash
# 1. Launch t3.medium instance (Ubuntu 20.04 AMI)
# 2. Create security group with inbound:
#    - SSH (22) from admin IP
#    - HTTP (80) from anywhere (reverse proxy)
#    - HTTPS (443) from anywhere
#    - Redis (6379) from internal only

# 3. SSH into instance
ssh -i key.pem ubuntu@instance-ip

# 4. Clone repo and install
sudo apt update && sudo apt install docker.io docker-compose git python3-pip
git clone <repo> && cd telegram_antifraud

# 5. Set up secrets management
# Use AWS Secrets Manager instead of .env

# 6. Start with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# 7. Setup reverse proxy (nginx)
sudo apt install nginx
# Configure nginx to forward to http://localhost:8000
```

#### On Kubernetes (Advanced):
```bash
# Deploy using Helm charts (todo: create helm/ directory)
helm install antifraud ./helm/antifraud \
  --set telegram.token_public=$TOKEN_PUBLIC \
  --set telegram.token_private=$TOKEN_PRIVATE \
  --set postgresql.host=postgres-service
```

---

## 2. Monitoring

### 2.1 System Health Dashboard

**Regular Checks (Every Hour):**
```bash
# Check service status
docker-compose ps

# Check resource usage
docker stats --no-stream

# Verify Redis connection
redis-cli -u $REDIS_URL PING  # Should return "PONG"

# Verify database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
```

**Daily Dashboard Review:**
- Open http://your-domain:8000/api/stats
- Check metrics:
  - Total users monitored
  - Users in restricted/banned status
  - Actions taken today
  - False positive rate

### 2.2 Key Metrics to Monitor

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Worker Error Rate | < 1% | 1-5% | > 5% |
| Message Processing Latency | < 100ms | 100-500ms | > 500ms |
| Redis Memory | < 70% | 70-85% | > 85% |
| DB Query Time | < 200ms | 200-500ms | > 500ms |
| Moderator Response Time | < 24h | 24-48h | > 48h |

### 2.3 Setting Up Alerts (Prometheus + Grafana)

### 2.4 Automated Backups

A simple script `tools/backup.py` is included for scheduled database and Redis
backups. Run it from a cronjob or Windows task every 4–6 hours:

```sh
python tools/backup.py \
    --pg-dsn "postgresql://user:pass@db/antifraud" \
    --redis-url "redis://redis:6379" \
    --out /var/backups/telegram_antifraud
```

The script uses `pg_dump` (custom format) and triggers a `BGSAVE` on Redis, then
copies `dump.rdb` to the output directory with a timestamp. Ensure `pg_dump` is
installed and `redis-py` is available in the Python environment.

Backups can be pushed to S3 or another object store by wrapping this script or
using standard tools; credentials may be provided via AWS environment variables.

Periodic restore drills are recommended (see §4.2 Disaster Recovery).

### 2.3 Setting Up Alerts (Prometheus + Grafana)

**Prerequisites:**
```bash
# Prometheus collects metrics from /metrics endpoint
# Grafana visualizes them

docker-compose -f docker-compose.monitoring.yml up -d
```

**Alert Rules** (prometheus/rules.yml):
```yaml
groups:
  - name: antifraud
    rules:
      - alert: HighErrorRate
        expr: rate(worker_errors_total[5m]) > 0.05
        for: 10m
        annotations:
          summary: "Worker error rate > 5%"
          
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 5m
        annotations:
          summary: "Database unreachable"
```

**Grafana Dashboards:**
- Download [sample dashboard JSON](https://grafana.com/grafana/dashboards)
- Import to Grafana: Administration → Dashboards → Import → Paste JSON
- Set data source to Prometheus

### 2.4 Log Management

**Viewing Logs:**
```bash
# Docker logs (last 100 lines)
docker-compose logs --tail=100 worker

# Follow logs in real-time
docker-compose logs -f worker

# Filter by keyword
docker-compose logs worker | grep ERROR
```

**Centralized Logging (ELK Stack - Optional):**
```bash
# Elasticsearch → Logstash → Kibana setup
# Configure filebeat to ship logs to Elasticsearch
docker-compose -f docker-compose.elk.yml up -d
```

**Log Retention Policy:**
- Worker logs: 30 days (rotate daily)
- Audit logs: indefinite (compressed after 90 days)
- PostgreSQL logs: 7 days
- Redis logs: 7 days

---

## 3. Maintenance

### 3.1 Regular Maintenance Schedule

| Task | Frequency | Owner | Duration |
|------|-----------|-------|----------|
| Security updates | Monthly | DevOps | 30 min |
| Database backup | Daily | Automation | 5 min |
| Rule review | Weekly | Moderator Sr. | 30 min |
| Dependency audit | Monthly | DevOps | 30 min |
| Moderator training | Quarterly | Admin | 1 hour |

### 3.2 Backup & Recovery

**Automated Daily Backup:**
```bash
# Add to crontab (runs at 2 AM daily)
0 2 * * * backup_postgres.sh

# backup_postgres.sh:
#!/bin/bash
pg_dump $DATABASE_URL > /backups/antifraud-$(date +%Y%m%d).sql
gzip /backups/antifraud-$(date +%Y%m%d).sql
aws s3 cp /backups/antifraud-*.sql.gz s3://backups/antifraud/
```

**Recovery Procedure:**
```bash
# 1. Restore from latest backup
gunzip /backups/antifraud-20260303.sql.gz
psql $DATABASE_URL < /backups/antifraud-20260303.sql

# 2. Verify integrity
SELECT COUNT(*) FROM users;  # Should match backup count

# 3. Restart services
docker-compose restart worker
```

### 3.3 Dependency Updates

**Monthly Security Audit:**
```bash
# Check for vulnerabilities
pip install safety
safety check

# If vulnerabilities found:
pip install --upgrade <package>  
# Test in staging first, then deploy
```

**Terraform/IaC Updates (if using cloud):**
```bash
terraform plan  # Dry-run to see changes
terraform apply  # Apply changes
```

### 3.4 Rule Updates

**Testing New Rules (without production impact):**
```bash
# 1. Create new rule in rules.json

# 2. Test with traffic simulator
python tools/traffic_simulator.py --attack spam --chat <TEST_CHAT>

# 3. Check if rule fired correctly
docker-compose logs worker | grep "rule_fired"

# 4. If OK, deploy to production
# If not OK, adjust and re-test

# 5. Document change in audit log
# (automatically logged via dashboard API)
```

---

## 4. Troubleshooting

### 4.1 Common Issues

#### Issue: Public bot not responding to messages

**Symptoms:**
- Messages sent in chat, bot doesn't react
- No logs in `docker-compose logs public_bot`

**Resolution:**
```bash
# 1. Check bot token validity
python -c "from pyrogram import Client; app = Client('test', api_id=123, api_hash='abc', bot_token='$TOKEN_PUBLIC'); app.start(); print('✅ Token valid')"

# 2. Verify bot is in chat
curl "https://api.telegram.org/bot$TOKEN_PUBLIC/getMe" | jq .result.username

# 3. Check Redis connection
docker-compose logs redis | tail

# 4. Restart publicly bot
docker-compose restart public_bot
```

---

#### Issue: Workers not processing messages (queue piling up)

**Symptoms:**
- Redis data_bus queue size growing
- No actions being taken
- Messages showing in logs but scores not calculated

**Resolution:**
```bash
# 1. Check worker health
docker-compose logs worker | tail -50

# 2. Check for exceptions
docker-compose logs worker | grep -i error

# 3. Verify database is accessible
docker-compose logs worker | grep -i postgres

# 4. If DB down, restart it
docker-compose restart postgres

# 5. If still stuck, clear queue (CAREFUL - data loss)
redis-cli FLUSHDB  # Production backup first!

# 6. Restart worker
docker-compose restart worker
```

---

#### Issue: Dashboard API returning 500 errors

**Symptoms:**
- http://localhost:8000/api/users returns HTTP 500
- Error response shows database connection issue

**Resolution:**
```bash
# 1. Check FastAPI logs
docker-compose logs dashboard

# 2. Verify PostgreSQL is running
docker-compose exec postgres psql -U postgres -c "SELECT 1"

# 3. Check connection string in .env
cat .env | grep DATABASE_URL

# 4. Test connection directly
python -c "import sqlalchemy; engine = sqlalchemy.create_engine('$DATABASE_URL'); engine.connect(); print('✅ OK')"

# 5. Restart dashboard
docker-compose restart dashboard
```

---

#### Issue: High memory usage in Redis

**Symptoms:**
- `docker stats` shows Redis using > 2 GB RAM
- System becoming slow

**Resolution:**
```bash
# 1. Check memory usage
redis-cli INFO memory | grep used_memory_human

# 2. Analyze key sizes
redis-cli --bigkeys

# 3. If signals/scores queue too large, investigate:
# - Maybe worker crashed and queue piled up?
# - Maybe data_bus has expired keys not being cleaned?

# 4. Set automatic key expiration
redis-cli EXPIRE data_bus 86400  # 24-hour TTL for queue

# 5. If still high, dump and analyze
redis-cli BGSAVE
# Then analyze RDB file
```

---

### 4.2 Performance Optimization

| Bottleneck | Metric | Solution |
|-----------|--------|----------|
| API slow | > 500ms per request | Add response caching, upgrade DB instance |
| High latency | Messages delayed > 2s | Increase worker replicas, optimize scoring algorithm |
| CPU high | > 80% usage | Profile code with py-spy, identify expensive operations |
| Memory leak | OOM after 1 week | Check for unclosed connections, use memory_profiler |

**Profiling Example:**
```bash
# Install py-spy (zero-overhead profiler)
pip install py-spy

# Profile worker for 30 seconds
py-spy record -o profile.svg -- python engine/worker.py

# Analyze CPU usage
py-spy top -- python engine/worker.py
```

---

## 5. Incident Response

### 5.1 Incident Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|----------------|---------|
| P1 (Critical) | System down, data loss | Immediate (5 min) | Database corrupted, all bots offline |
| P2 (High) | Significant degradation | 30 minutes | Worker errors > 10%, API timeouts |
| P3 (Medium) | Minor issue, workaround exists | 4 hours | One rule not firing, single moderator locked out |
| P4 (Low) | Non-urgent, cosmetic | 1 business day | Dashboard typo, missed email notification |

### 5.2 Incident Response Playbook

**Step 1: Detect & Alert (0-2 min)**
```
- Automated alert fires OR
- User reports issue
- Page on-call engineer
```

**Step 2: Triage (2-5 min)**
```bash
# 1. Verify problem
docker-compose ps | grep -v Up  # Any down services?
docker stats  # CPU/memory problems?

# 2. Assess impact
- Is this affecting moderation decisions?
- Are users able to use the system?
- Is data at risk?

# 3. Assign severity based on impact
- No active chats? P4 (can wait)
- Chat active but can moderate manually? P3
- Can't kick/mute? P2 (moderators can't do jobs)
- Data loss? P1 (emergency)
```

**Step 3: Containment (5-15 min)**

For P1 emergencies:
```bash
# Option A: Scale down automated actions (emergency mode)
docker-compose exec worker python -c "
import redis
r = redis.from_url('$REDIS_URL')
r.set('emergency_mode', 'true')  # Worker checks this flag
"
# Worker will still detect but won't auto-kick (manual review only)

# Option B: Isolate affected component
docker-compose stop worker  # Prevent cascading failures

# Option C: Switch to backup
# Pre-deployed standby system takes over
```

**Step 4: Resolution (depends on issue)**
```bash
# Fix (e.g., restart service)
docker-compose restart worker

# Verify recovery
curl http://localhost:8000/api/health

# Monitor for 10 minutes to ensure stable
docker-compose logs -f worker | grep -E "(ERROR|ProcessingComplete)"
```

**Step 5: Post-Incident**
```bash
# 1. Document in incident log
cat >> incidents.log << EOF
2026-03-03 14:30 - Worker OOM
Impact: 5 min no processing
Cause: Memory leak in clustering code
Fix: Restart + code review scheduled
EOF

# 2. Root cause analysis (within 24 hours)
# What went wrong?
# Why didn't we catch it?
# How do we prevent recurrence?

# 3. Create ticket for permanent fix
# Add to product backlog
```

### 5.3 Escalation Matrix

```
Public Bot Down
├─ → Worker down → Restart worker
├─ → Redis down → Restart Redis + verify data
└─ → Telegram API down → Page on-call, nothing we can do

Private Bot Down
├─ → PostgreSQL/permissions issue → Restart, check perms
├─ → Network issue → Check firewall, host connectivity
└─ → Rate limited → Back off, check token limits

Dashboard API Down
├─ → FastAPI crashed → Check logs, restart
├─ → DB connection lost → Verify DB running + connection string
└─ → Port already in use → Kill process on :8000

Data Loss
└─ → Database corrupt → RESTORE FROM BACKUP
    → Restore timestamp
    → Verify integrity
    → Post-mortem on cause
    → Improve backup testing
```

---

## 6. Escalation Contacts

### 6.1 On-Call Rotation

**Monday-Friday (Business Hours)**
- Primary: Operations Lead (9 AM - 5 PM)
- Secondary: Senior Engineer

**Nights & Weekends (On-Call Duty)**
- Rotation of 3 engineers (1 week each)
- Call out via PagerDuty

### 6.2 Contact Information

| Role | Name | Email | Phone | Slack |
|------|------|-------|-------|-------|
| Ops Lead | [Name] | ops@example.com | +1-xxx-xxxx | @ops_lead |
| Security | [Name] | security@example.com | +1-xxx-xxxx | @security |
| Database Admin | [Name] | dba@example.com | +1-xxx-xxxx | @dba |
| DevOps Lead | [Name] | devops@example.com | +1-xxx-xxxx | @devops |

### 6.3 Escalation Criteria

**When to escalate:**
- Production data loss
- > 30 min downtime
- User data breach
- Compliance violation
- Police investigation

**Escalation path:**
```
On-Call Engineer
    ↓
Escalate if > 15 min unresolved
    ↓
Engineering Manager
    ↓
Escalate if might impact legal
    ↓
Compliance Officer
    ↓
CEO (data breach/police)
```

---

### 6.4 Emergency Contacts

**Telegram Support:** `@BotFather` (for API issues)  
**Infrastructure Provider:** [AWS/GCP/Azure support number]  
**Security: ** security@example.com (GPG key: ...)  
**Status Page:** http://status.example.com

---

## Appendix: Useful Commands

```bash
# Quick health check
docker-compose ps && docker-compose exec redis redis-cli PING && echo "✅ All OK"

# Clear cache (use with caution)
redis-cli FLUSHDB  # Empties Redis

# Backup production database
pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz

# Tail logs for specific service
docker-compose logs -f worker | grep "ERROR"

# Check specific error
docker-compose logs worker | grep "NoneType" -A 5  # Show 5 lines after error

# SSH into container
docker-compose exec worker bash

# Run one-off command in container
docker-compose exec worker python script.py

# Rebuild image (if Dockerfile changed)
docker-compose build worker
docker-compose up -d worker

# Get container statistics
docker stats --no-stream

# Prune old images/volumes
docker system prune -a
```

---

**Versión del Documento:** 1.0  
**Última Actualización:** 2026-03-03  
**Próxima Revisión:** 2026-06-03  
**Responsable:** hasbulla team
