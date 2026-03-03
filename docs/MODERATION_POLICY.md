# Políticas de Moderación y Gobernanza

## 1. Principios Rectores

### 1.1 Seguridad de la Comunidad
- Proteger la integridad del chat contra operadores de múltiples cuentas, spam y estafadores.
- Minimizar falsables positivos (bans injustificados) mediante auditoría humana.
- Escalada proporcional: warnings → restricciones → salida del grupo.

### 1.2 Transparencia
- Todo veto o restricción debe estar documentado con razón y contexto.
- Moderadores pueden revisar el histórico de decisiones (audit trail).
- Los usuarios pueden apelar acciones dentro de 7 días.

### 1.3 Privacidad
- No almacenar texto completo de mensajes privados; solo hashes y metadatos.
- Cumplir con GDPR/CCPA: derecho a olvidar (borrar perfil tras 90 días inactivos).
- Encripción de datos sensibles en reposo.

---

## 2. Clasificación de Comportamientos

### 2.1 Nivel 1: Advertencia (Score 10-30)
**Ejemplos:**
- Primer mensaje con enlace
- Frecuencia moderada (15-20 msg/hora)

**Acción:** Log + notificación al usuario
**Duración:** Sin restricción

### 2.2 Nivel 2: Restricción Suave (Score 30-50)
**Ejemplos:**
- Velocidad alta (30-50 msg/hora)
- Mensajes similares repetidos
- Usuarios nuevos con honeypot

**Acción:** Shadow mute (1-4 horas)
**Duración:** Automática, sin notificación pública

### 2.3 Nivel 3: Restricción Media (Score 50-80)
**Ejemplos:**
- Muy alta velocidad (>50 msg/hora)
- Múltiples honeypots
- Parte de un cluster/red

**Acción:** Restricción oficial (enlazar, votación)
**Duración:** 24 horas

### 2.4 Nivel 4: Expulsión Temporal (Score 80-120)
**Ejemplos:**
- Conducta de raid coordinada
- Phishing / engaños
- Abuso de bot conocido

**Acción:** Kick del chat
**Duración:** 7 días (banlist temporal)

### 2.5 Nivel 5: Expulsión Permanente (Score > 120)
**Ejemplos:**
- Reincidencia tras 2+ kicks
- Estafa confirmada
- Operador profesional de multicuentas

**Acción:** Ban permanente del usuario
**Duración:** Indefinida (remoción manual de ban tras apelación humana)

---

## 3. Procesos de Auditoría

### 3.1 Revisión Automática (24/7)
- Dashboard en vivo muestra alertas en tiempo real.
- Moderador puede inspeccionar usuario antes de actuar.
- Necesida de confirmación humana para kicks/bans.

### 3.2 Revisión Semanal
- Listado de falsables positivos (usuarios con score alto pero sin acciones reales).
- Estadísticas de cobertura (% de raids detectados).
- Reporte de cambios en rules.

### 3.3 Apelación
- Usuario puede escribir privado al bot: `/appeal <razon>`.
- Ticket abierto en sistema interno.
- Moderador revisa historico + contexto.
- Decisión en 48 horas.

---

## 4. Checklist de Cumplimiento ToS

### 4.1 Telegram ToS
- ✅ No usar bots para spam masivo (máx 5K chats/mes)
- ✅ Respetar rate limits (100 msg/min por chat)
- ✅ No interceptar/guardar mensajes privados
- ✅ Usar API oficial (pyrogram) no scraping
- ✅ Avisar claramente que es antifraud automático

### 4.2 GDPR (si hay usuarios EU)
- ✅ Privacidad by design: solo datos mínimos (ID, score, acciones)
- ✅ Derecho a acceso: moderador puede exportar perfil usuario
- ✅ Derecho a olvidar: borrar perfil tras 90 días sin actividad
- ✅ Consentimiento: notificar al user que se monitoriea

### 4.3 CCPA (si hay usuarios USA)
- ✅ Disclose data collection practices
- ✅ Opt-out para crawling de datos
- ✅ No sell user data a terceros

### 4.4 Prácticas Justas
- ✅ Disclosure: informar que es antfraud
- ✅ No discriminación: mismos criterios para todos
- ✅ Proporcionalidad: restricciones acordes al riesgo
- ✅ Apelación: mecanismo claro de reclamo

---

## 5. Responsabilidades por Rol

### 5.1 Moderador Jr.
- Ver alertas en vivo
- Revisar perfiles de usuarios sospechosos
- **NO** ejecutar kicks directamente (solo si score > 100)
- Reportar falsos positivos

### 5.2 Moderador Sr.
- Aprobar kicks/bans
- Crear/editar reglas con aprobación supervisor
- Revisar apelaciones
- Auditoría semanal

### 5.3 Admin/Supervisor
- Aprobar cambios en reglas críticas
- Resolver apelaciones de alto nivel
- Gestionar permisos de moderadores
- Reportes al propietario del chat

---

## 6. Políticas Específicas

### 6.1 Operadores Multicuenta
**Definición:** Usuario que controla 3+ cuentas en el mismo chat.

**Indicadores:**
- Mismo IP (si disponible)
- Patrones similares de mensajes
- Se unen simultáneamente (1-5 min apart)
- Misma red/cluster (engine/clusters.py)

**Acción:**
1. Kick a todos
2. Ban temporal 7 días
3. Si reincide → ban permanente

### 6.2 Spam / Estafas
**Definición:** Mensajes promoviendo productos falsos, servicios de pago, phishing.

**Indicadores:**
- Honeypot detector activo
- Keywords: "WhatsApp", "contactar", "compra", "oferta"
- Enlaces acortados desconocidos
- Similitud alta a comentarios anteriores

**Acción:**
1. Kick inmediato
2. Ban 30 días
3. Notificar a canal de seguridad

### 6.3 Raids
**Definición:** >15 usuarios nuevos uniéndose en <5 min.

**Indicadores:**
- Spike en joins (engine/raid.py)
- Primeros mensajes son spam/honeypot
- Similar IP / info de perfil

**Acción:**
1. Activar "slow mode" (1 msg/min)
2. Kick a todos si cluster > 50% es spam
3. Ban permanente si jefe de raid identificado

### 6.4 Usuarios Legítimos
**Criterios para "whitelist":**
- Usuario activo > 30 días
- Historial limpio (0 warnings)
- Contribuye valor (info útil/moderación)

**Beneficios:**
- Score multiplicado por 0.5 (umbral más alto)
- Bypass de shadow mute
- Apelación prioritaria

---

## 7. Transparencia y Comunicación

### 7.1 Notificación al Usuario
Cuando un usuario es kickeado:

```
Bot [automod]: User @spam123 was removed from chat.
Reason: Spam detected (score 85/100)
Appeal: Reply /appeal to contest
```

### 7.2 Reporte Público Semanal
En canal de auditoría/logs:
```
📊 Antifraud Weekly Report
- Messages scanned: 150K
- Users monitored: 5K
- Users actioned: 23
  - Muted: 15
  - Kicked: 8
- Raids detected: 2
- False positives: 1 (0.7%)
```

### 7.3 Escalamientos
- Falso positivo en ban → revisión automática
- Spam evasión (vuelve con nueva cuenta) → notificar admin chat
- Ataque coordinado → deshabilitar chats temporalmente

---

## 8. Métricas de Éxito

| Métrica | Meta | Frecuencia |
|---------|------|-----------|
| Tasa de detección de raids | > 85% | Semanal |
| Falsos positivos (bans correctos) | < 5% | Semanal |
| Tiempo respuesta a apelación | < 48h | Per appeal |
| Reincidencia post-kick | < 20% | Mensual |
| Satisfacción moderador | > 4/5 | Trimestral |

---

## 9. Incidentes y Escalación

### 9.1 Incidente de Seguridad
1. Alertar a admin inmediatamente
2. Freeze ban list (no bans nuevos temporalmente)
3. Audit log completo
4. Post-mortem en 24h

### 9.2 Fallo de Spam
- > 10 mensajes spam por hora sin detectar
- →Revisar reglas honeypot
- → Ajustar templates si es brecha conocida

### 9.3 Coordinación Multi-Chat
- Si spam es coordinado entre chats
- → Compartir bloklists
- → Considerar ban a nivel de red Telegram

---

## 10. Revisión de Políticas

- **Trimestral:** Revisar métricas, ajustar umbrales
- **Anual:** Auditoría externa, actualizar ToS
- **Ad-hoc:** Cambios en patrones de ataque

---

**Última revisión:** 2026-03-03  
**Próxima revisión:** 2026-06-03  
**Responsable:** hasbulla team
