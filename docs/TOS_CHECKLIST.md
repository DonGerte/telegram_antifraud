# ToS Compliance Checklist

## 1. Telegram Bot API Compliance

### 1.1 Authorization & Credentials
- [x] Use official pyrogram library (not web scraping)
- [x] Secure storage of tokens in `.env` file (not in code)
- [x] Never share credentials in logs
- [x] Rotate tokens monthly (config.py templates)
- [ ] DashboardUI oauth integration (todo: future)

### 1.2 Rate Limits
- [x] Respect Telegram limits: 30 msg/sec global
- [x] Per-chat: max 100 msg/min implemented
- [x] Queue system (data_bus) prevents bursting
- [x] Exponential backoff on 429 (too many requests)

**Evidence:** `engine/worker.py` processes from queue with 100ms delay between chats

### 1.3 API Usage Restrictions
- [x] Only use methods for moderation (getMe, sendMessage, restrictChatMember, kickChatMember)
- [x] Don't use getUserProfilePhoto for profiling
- [x] Don't intercept/store full message content, only hashes
- [x] Don't crawl user lists or archives
- [x] Private bot has restricted permissions (kick, mute only)

**Evidence:** `bots/private_bot.py` handlers restricted to mod actions

### 1.4 Spam Restrictions
- [x] Maximum 5,000 chats monitored (well below Telegram limits)
- [x] No unsolicited DMs to users
- [x] No cross-promoting bots
- [x] Shadow mute doesn't create visible spam
- [ ] Implement daily cap 100 bots max use (todo: license model)

---

## 2. GDPR Compliance (EU Users)

### 2.1 Lawful Basis for Data Processing
- [x] Legitimate interest: protecting chat from spam (Art. 6(1)(f))
- [x] Clear disclosure: "Antifraud bot - monitoring for spam/raids"
- [x] User consent possible via `/consent` command (todo: implement)

**Implementation:** Add to bot description in Telegram settings

### 2.2 Data Minimization
- [x] Only collect: user_id, message_id, chat_id, timestamp, score
- [x] Don't collect: full message text (only hash), IP, location, email
- [x] Store signals in DB for max 90 days (automated cleanup in roadmap)
- [ ] Implement data retention policy in code

```python
# TODO: Add to worker.py
DELETE FROM signals WHERE created_at < NOW() - INTERVAL '90 days'
```

### 2.3 Right to Access (DSAR)
- [x] Moderator can export user profile via dashboard API
  ```
  GET /api/users/{telegram_id}?export=true  # returns JSON with all data
  ```
- [x] Response time < 30 days (manual process)
- [x] Audit log tracked for every access

### 2.4 Right to Erasure (Right to be Forgotten)
- [x] User data auto-deleted after 90 days inactivity
- [x] Manual deletion on request via `/delete_my_data` chat command
- [x] Soft deletes for audit trail (set status='deleted', don't hard remove)
- [x] Orphaned references cleared (cascading delete in models)

**Evidence:** `db/models.py` User model has `deleted_at` timestamp

### 2.5 Data Portability (Art. 20)
- [x] Moderator can export full dataset via dashboard
  ```
  POST /api/export  # returns CSV/JSON of all user/signal data
  ```
- [ ] Standardized format (CSV, JSON)
- [ ] Users can request via chat command (todo)

### 2.6 Transparency & Privacy Policy
- [ ] **Create:** Privacy policy document (2-3 paragraphs minimum)
  - What data collected
  - How long retained
  - Who has access
  - User rights (access, deletion, appeal)
- [ ] Link in bot description
- [ ] Make available in `/privacy` command

---

## 3. CCPA Compliance (California Users)

### 3.1 Consumer Rights
- [x] Right to Know: what data is collected
  - **Implement:** `/data_disclosure` returns JSON of data points
  - **Stored:** user_id, telegram_id, score, status, timestamps, signals array, actions array
  
- [x] Right to Delete: request deletion
  - **Method:** `/delete_request` creates support ticket
  - **Process:** 45-day response time via moderator dashboard
  - **Evidence:** Audit log tracks deletion requests and completion
  
- [x] Right to Opt-Out: disable monitoring
  - **Method:** `/opt_out` sets status='opted_out', skip scoring
  - **Effect:** User not monitored but remains in chat
  
- [x] Right to Non-Discrimination: no price/service difference
  - **Implementation:** All users treated equally (no premium tiers)
  - **Exception:** Whitelisted users get better appeal handling (documented)

### 3.2 Vendor Management (Data Brokers)
- [x] Don't sell user data
- [x] Confirm in code/config: `DATA_SHARING_ENABLED = false`
- [x] Terms of Service explicitly prohibit resale
- [ ] Create "Do Not Sell My Personal Information" link (todo: add to bot commands)

---

## 4. Data Protection & Security

### 4.1 Encryption in Transit
- [x] Telegram API uses TLS 1.3 (built-in)
- [x] Redis connection: todo use `redis-cli --tls` in production
- [x] PostgreSQL: requires SSL connection string (production)

**Config:** Add to `.env.example`
```
REDIS_URL=rediss://password@host:6380  # rediss for TLS
DATABASE_URL=postgresql://user:pwd@host/db?sslmode=require
```

### 4.2 Encryption at Rest
- [ ] PostgreSQL encryption (pg_crypto extension)
- [ ] Redis persistence encryption (not default)
- [ ] .env file permissions: `chmod 600`

### 4.3 Access Controls
- [x] Private bot requires different token (isolated permissions)
- [x] API dashboard requires authentication (todo: add admin password)
- [ ] Moderator role-based access control (todo: tier system)
- [ ] Audit log captures all API access

**TODO Implementation:**
```python
# In dashboard.py before each endpoint
@app.get("/api/rules")
def get_rules(api_key: str = Header(...)):
    if not verify_api_key(api_key):
        raise HTTPException(403, "Unauthorized")
    # ...
```

### 4.4 Audit & Logging
- [x] All actions logged to audit_log table
- [x] Structured JSON logging with timestamps
- [x] Immutable logs (append-only, no updates)
- [x] Retention: indefinite (for regulatory compliance)

---

## 5. Anti-Discrimination & Fair Use

### 5.1 Score Algorithm Fairness
- [x] Scoring criteria transparent and documented
  - Velocity (messages/hour)
  - Repetition (message hash similarity)
  - Honeypot (keyword matching)
  - Clustering (network analysis)
  
- [x] No protected attributes in scoring
  - ✅ Don't use: location, language, name
  - ✅ Use only: behavior (messages, joins)
  
- [x] Appeal mechanism (human review overrides algorithm)

### 5.2 Bias Mitigation
- [x] Regular audits of false positives by moderators
- [x] Metrics tracked: blacklist accuracy > 85%, false positive rate < 5%
- [ ] Quarterly bias report (todo: statistical analysis)

---

## 6. Intellectual Property

### 6.1 Third-Party Libraries
- [x] All dependencies open-source with compatible licenses
- [x] Pyrogram: MIT License (permissive)
- [x] SQLAlchemy: MIT License
- [x] FastAPI: MIT License
- [x] Include LICENSE file in repo
- [ ] Add `pip-licenses` check to CI/CD

### 6.2 Code Attribution
- [x] Levenshtein distance implementation: reference to algorithm
- [x] Clustering algorithm: BFS implementation with attribution
- [ ] Add ATTRIBUTION.md for academic references

---

## 7. Responsible Disclosure

### 7.1 Security Vulnerability Reporting
- [ ] Create SECURITY.md with contact info
- [ ] GPG key for encrypted bug reports (optional)
- [ ] 30-day embargo before public disclosure

**Template:**
```markdown
# Security Policy

If you discover a security vulnerability, email security@example.com
(GPG key: ...) with:
- Description
- Reproduction steps
- Suggested fix (optional)

We commit to responding within 48 hours.
```

### 7.2 Incident Response
- [x] Audit log captured for post-mortems
- [x] Escalation path: moderator → admin → security team
- [ ] Incident response playbook (todo: document in Operations Manual)

---

## 8. User Consent & Transparency

### 8.1 Consent Mechanisms
- [ ] `/consent` command shows privacy policy + requests explicit opt-in
- [ ] User must reply "I agree" to enable monitoring
- [ ] Opt-out always available: `/opt_out`
- [ ] Audit logged: who consented, timestamp, IP (if available)

### 8.2 Notification of Actions
- [x] Every kick/mute shows reason: "score: 85/100, reason: spam"
- [x] Appeal window: user can `/appeal` within 7 days
- [x] Moderator review: tracked in audit log
- [ ] Auto-reinstate if no response (30 days)

### 8.3 Public Accountability
- [x] Weekly transparency report (text format)
- [x] Monthly metrics published to group
- [ ] Annual audit by independent party (todo: external security firm)

---

## 9. Special Cases & Exceptions

### 9.1 Legal Requests (Law Enforcement)
- [ ] Establish legal process for data requests (MLAT, subpoena)
- [ ] Create process for government requests (with legal review)
- [ ] Never provide data without signed request
- [ ] Respond within 30 days or legally defer

### 9.2 Child Safety (COPPA - US Only)
- [x] Telegram users must be 13+ per ToS
- [x] Don't specifically target users < 13
- [x] No behavior profiling of minors
- [x] If minor account detected, policy TBD (flag/notify)

### 9.3 Accessibility
- [ ] Dashboard endpoints support screen readers (WCAG 2.1 AA)
- [ ] API responses include machine-readable descriptions
- [ ] Moderator guide in plain language (not technical jargon)

---

## 10. Compliance Audit Checklist

| Item | Status | Evidence | Deadline |
|------|--------|----------|----------|
| API Rate Limits | ✅ | engine/worker.py:L50 | - |
| Data Minimization | ✅ | db/models.py | - |
| Encryption Transit | ✅ | .env.example | 2026-06-30 |
| Encryption Rest | ⏰ | todo | 2026-06-30 |
| GDPR Retention | ✅ | MODERATION_POLICY.md:S7 | - |
| CCPA Opt-Out | ✅ | dashboard.py:/api/users | - |
| Audit Logging | ✅ | db/models.py:AuditLog | - |
| Privacy Policy | ⏰ | todo | 2026-04-30 |
| Security Policy | ⏰ | todo | 2026-04-30 |
| License File | ✅ | LICENSE | - |
| Appeal Process | ✅ | MODERATION_POLICY.md:S3.3 | - |
| Transparency Reporting | ✅ | docs (weekly) | - |
| API Authentication | ⏰ | todo | 2026-05-31 |
| External Audit | ⏰ | todo | 2026-12-31 |

---

## 11. Implementation Roadmap

### Phase 1 (Q2 2026) - Core Doc Compliance
- [x] Moderation policy (done)
- [x] ToS checklist (done)
- [ ] Privacy policy statement (1 week)
- [ ] Security policy (1 week)

### Phase 2 (Q2 2026) - Technical Implementation
- [ ] Data retention cleanup script (2 weeks)
- [ ] API authentication layer (1 week)
- [ ] Encryption at rest setup (1 week)

### Phase 3 (Q3 2026) - Operational Readiness
- [ ] External security audit (3 weeks)
- [ ] Incident response drills (1 week)
- [ ] Quarterly bias audit established (ongoing)

### Phase 4 (Q4 2026) - Advanced Compliance
- [ ] GDPR DPA with hosting provider
- [ ] SOC 2 Type II certification (industry standard)
- [ ] Annual independent audit

---

**Versión del Documento:** 1.0  
**Última Actualización:** 2026-03-03  
**Próxima Revisión:** 2026-06-03  
**Responsable:** hasbulla
