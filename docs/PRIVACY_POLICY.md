# Privacy Policy

**Last Updated:** March 3, 2026  
**Effective Date:** March 3, 2026  
**License:** MIT  
**Contact:** hasbullita007@gmail.com

---

## 1. Introduction

This **Telegram Antifraud Bot** ("Bot," "we," "us," or "our") values your privacy. This Privacy Policy explains:
- What data we collect
- How we use it
- How long we keep it
- Your rights

This policy applies to all users in chats where the Bot is active.

---

## 2. What Data We Collect

### 2.1 Automatically Collected When Posting Messages
- **User ID** (Telegram identifier)
- **Chat ID** (group identifier)
- **Message ID** (unique message reference)
- **Timestamp** (when message was sent)
- **Message hash** (SHA-256 digest, NOT the actual text)
- **Number of links** in message (count only, not URLs)
- **Message length** (character count)
- **User status** (new user, member since X)

### 2.2 Automatically Collected When Joining Chat
- **User ID**
- **Chat ID**
- **Join time** (exact timestamp)
- **User join history** (if visible)

### 2.3 NOT Collected
- ❌ Full message text
- ❌ Profile pictures or media files
- ❌ User location or IP address
- ❌ Private messages (only group messages)
- ❌ Email or phone number
- ❌ Payment information
- ❌ Device information

---

## 3. How We Use Your Data

### 3.1 Spam & Fraud Detection
- Analyze message velocity (messages per hour)
- Detect spam keywords via pattern matching
- Identify multi-account networks
- Detect raids (coordinated mass joins)

### 3.2 Safety & Moderation
- Flag suspicious accounts for moderator review
- Prevent scams and phishing
- Maintain group security
- Enforce group rules

### 3.3 Audit & Compliance
- Record moderation actions (kicks, mutes)
- Maintain appeal history
- Ensure transparency
- Support dispute resolution

### 3.4 NOT Used For
- ❌ Advertising or marketing
- ❌ Profiling behavior outside the chat
- ❌ Selling to third parties
- ❌ Training AI models
- ❌ Sharing with external services

---

## 4. Data Retention

| Data Type | Retention | Deletion Method |
|-----------|-----------|-----------------|
| Signals (spam scores) | 90 days | Automatic purge |
| User profiles | Until opt-out or inactivity | Soft delete (retained for audit) |
| Moderation actions | Indefinite | Never (legal compliance) |
| Audit logs | Indefinite | Immutable (tamper-proof) |
| Appeals | 2 years | After final decision |

**Default:** User data cleared automatically after 90 days without messages.

---

## 5. Your Rights

### 5.1 Right to Know
You can request what data we have about you:
- **Command:** `/data_disclosure`
- **Response:** JSON file with all collected data
- **Format:** User ID, scores, signals, actions, timestamps
- **Timeframe:** Instant (automated response)

### 5.2 Right to Deletion
You can request permanent deletion of your profile:
- **Command:** `/delete_my_data`
- **Process:** Creates deletion request ticket
- **Timeframe:** 30 days (manual review)
- **Result:** All personal data removed from active systems

*Note: Audit logs retained for legal compliance (cannot be deleted).*

### 5.3 Right to Opt-Out
You can disable monitoring while staying in the chat:
- **Command:** `/opt_out`
- **Effect:** You won't be scored or flagged
- **Reversal:** `/opt_in` to re-enable
- **Timeframe:** Instant

### 5.4 Right to Appeal
You can contest moderation actions:
- **Command:** `/appeal <reason>`
- **Process:** Moderator human review
- **Timeframe:** 48 hours response
- **Outcome:** Decision logged in audit trail

---

## 6. Data Security

### 6.1 Technical Safeguards
- **Encryption in Transit:** Telegram API uses TLS 1.3
- **Access Control:** Only moderators and Bot admins can view data
- **Database Encryption:** PostgreSQL with encryption at rest (production)
- **Sealed Logs:** Audit trail is append-only (immutable)

### 6.2 Human Safeguards
- **Need-to-Know:** Only moderators with specific role access data
- **Training:** All moderators sign confidentiality agreements
- **Monitoring:** Admin oversight of all data access
- **Incident Response:** Security team notified of breaches

---

## 7. Third-Party Services

### 7.1 Telegram (Platform)
- **Role:** Chat platform where Bot operates
- **Data Shared:** User ID, message metadata (Telegram ToS compliance)
- **Privacy:** Review [Telegram Privacy Policy](https://telegram.org/privacy)

### 7.2 Redis (Message Queue)
- **Role:** Temporary message buffer (< 1 second)
- **Data Shared:** Unprocessed messages (flushed after action)
- **Retention:** 0 days (ephemeral)

### 7.3 PostgreSQL (Storage)
- **Role:** Persistent audit & scoring database
- **Data Shared:** User profiles, signals, actions, audit logs
- **Location:** Hosted on [Provider – todo: specify]
- **Encryption:** AES-256 at rest

### 7.4 NO Third-Party Data Sales
- We do **not** sell, rent, or share personal data
- We do **not** use data brokers
- We do **not** allow ads based on Bot data

---

## 8. Regional Privacy Laws

### 8.1 GDPR (European Union / EEA Users)
**Your Rights:**
- Right to Access (Art. 15): `/data_disclosure`
- Right to Erasure (Art. 17): `/delete_my_data`
- Right to Rectification (Art. 16): Contact moderator for inaccuracies
- Right to Restrict Processing (Art. 18): `/opt_out`
- Right to Data Portability (Art. 20): Export via dashboard API

**Legal Basis:** Legitimate interest (Art. 6(1)(f)) – preventing spam/fraud

**Data Protection Officer:** [todo: specify contact]

**Data Processing Agreement:** Available upon request for organizations

### 8.2 CCPA (California Residents)
**Your Rights:**
- Right to Know: `/data_disclosure`
- Right to Delete: `/delete_my_data`
- Right to Opt-Out: `/opt_out`
- Non-Discrimination: No penalties for exercising rights

**Our Commitment:**
- ✅ We don't sell personal information
- ✅ We don't discriminate based on privacy choices
- ✅ We respond within 45 days of verified requests

### 8.3 PIPEDA (Canada)
- Personal information protected under Canadian privacy law
- Same rights as GDPR (access, correction, deletion)
- Contact: [todo: specify privacy officer]

---

## 9. Changes to This Policy

We may update this Privacy Policy:
- **Notice:** Bot will announce major changes in the chat
- **Timeframe:** 30 days before changes take effect
- **Archive:** Previous versions available upon request
- **Contact:** [todo: specify contact method]

---

## 10. Contact & Complaints

### 10.1 Questions About This Policy
- **Email:** [privacy@example.com]
- **Chat Command:** `/privacy` for policy summary
- **Response Time:** 7 days

### 10.2 Privacy Complaints
If you believe your rights are violated:

1. **Step 1:** Contact us at [privacy@example.com]
   - Describe the issue
   - Include relevant dates/Chat ID
   
2. **Step 2:** We investigate (14 days)
   - Review audit logs
   - Consult with moderators
   
3. **Step 3:** You receive our response
   - Explanation of what happened
   - Actions taken
   - Appeal option if unsatisfied

### 10.3 Regulatory Complaints
- **EU/EEA:** File complaint with your local Data Protection Authority
- **California:** File complaint with [CCPA Attorney General](https://oag.ca.gov)
- **Canada:** File complaint with [Privacy Commissioner](https://www.priv.gc.ca)

---

## 11. Definitions

- **Personal Data:** Any information related to an identified user
- **Processing:** Collection, use, storage, deletion of personal data
- **Legitimate Interest:** Balancing our interests (safety) with your privacy
- **Data Minimization:** Collecting only necessary data
- **Pseudonymization:** Using IDs instead of names (user_id, not "John")

---

## 12. Frequently Asked Questions

### Q: Does the Bot read my messages?
**A:** No. We only store a hash (irreversible fingerprint) and count links, not the actual text.

### Q: Can I be tracked outside the chat?
**A:** No. We only process chat data, not across Telegram or external services.

### Q: How long before my data is deleted?
**A:** 90 days of inactivity by default. You can request immediate deletion: `/delete_my_data`

### Q: Can moderators see my full messages?
**A:** No. They see signal flags (score, reason), not message content.

### Q: What if I disagree with a moderation action?
**A:** Use `/appeal` to request human review. Your case is reviewed within 48 hours.

### Q: Is my data encrypted?
**A:** Yes. Telegram API uses TLS 1.3 (in transit) and databases encrypted at rest (production).

### Q: Who else has access to my data?
**A:** Only Bot admins and assigned moderators. Access is audit-logged.

---

## 13. Appendix: Technical Details

### 13.1 Data Minimization Examples

**Example 1: Message Spam Detection**
```
Input message: "WOW! Click here for FREE crypto!!! https://shorturl.xyz/abc"

We store:
- user_id: 123456
- chat_id: -100987654
- timestamp: 2026-03-03T14:23:45Z
- message_hash: 5d41402abc4b2a7...  # irreversible
- link_count: 1
- is_spam: true  # prediction only

We DO NOT store:
- "WOW! Click here for FREE crypto!!" (full text)
- https://shorturl.xyz/abc (URL)
```

**Example 2: Join Event**
```
Input: User joins chat

We store:
- user_id: 123456
- chat_id: -100987654
- join_time: 2026-03-03T14:00:00Z
- is_new_user: true

We DO NOT store:
- user's first name / username
- profile picture
- account creation date
- bio / about section
```

### 13.2 Hash Function
- **Algorithm:** SHA-256 (NIST standard)
- **Property:** One-way – cannot reverse to get original message
- **Use:** Detect repeated spam without storing text
- **Example:**
  ```
  "Cheap Viagra!" -> SHA-256 -> 3a7bd3e... (always same hash)
  Different text -> different hash
  ```

---

**Version:** 1.0  
**Status:** APPROVED  
**Next Review:** June 3, 2026
