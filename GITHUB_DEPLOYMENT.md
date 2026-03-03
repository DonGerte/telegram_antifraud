# Instrucciones de Deployment a GitHub

## Previa: Configuración de Git

### 1. Verificar que Git esté instalado
```bash
git --version
```

### 2. Configurar credenciales de Git (primera vez)
```bash
git config --global user.name "hasbulla"
git config --global user.email "hasbulla@example.com"
```

---

## Opción A: Crear Nuevo Repositorio en GitHub

### 1. Crear repositorio en GitHub.com
1. Ve a https://github.com/new
2. Nombre: `telegram_antifraud`
3. Descripción: "Production-ready Telegram anti-fraud system"
4. Privado/Público: Elige según necesites
5. **NO inicialices con README** (ya tienes uno)
6. Click "Create repository"

### 2. Verificar que no hay cambios sin comitear
```bash
cd C:\workspace\telegram_antifraud
git status
```

Si hay cambios pendientes:
```bash
git add -A
git commit -m "feat: add Grafana, React UI, A/B testing, PagerDuty, SOC2 roadmap"
```

### 3. Conectar repositorio local con GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/telegram_antifraud.git
```

Verifica:
```bash
git remote -v
# Debe mostrar:
# origin  https://github.com/YOUR_USERNAME/telegram_antifraud.git (fetch)
# origin  https://github.com/YOUR_USERNAME/telegram_antifraud.git (push)
```

### 4. Subir todo a GitHub
```bash
git branch -M main
git push -u origin main
```

Te pedirá autenticación:
- **Usuario:** Tu username de GitHub
- **Contraseña:** Tu token de acceso personal (PAT)

[Cómo crear PAT en GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

## Opción B: Si ya tienes repo local con Git

```bash
cd C:\workspace\telegram_antifraud

# Verificar estado
git status

# Agregar todos los archivos nuevos
git add -A

# Comitear cambios
git commit -m "feat: complete system with Grafana, React, A/B testing, PagerDuty, SOC2"

# Cambiar rama a 'main' si la tienes como 'master'
git branch -M main

# Subir a GitHub
git push -u origin main
```

---

## Opción C: Migrar desde otro repositorio

Si ya tenías un repo:

```bash
cd C:\workspace\telegram_antifraud

# 1. Cambiar origin
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/telegram_antifraud.git

# 2. Subir
git push -u origin main
```

---

## Verificar Upload

```bash
# Verificar que fue a GitHub
git log --oneline | head -5

# Verifica en el browser:
# https://github.com/YOUR_USERNAME/telegram_antifraud
```

---

## Comandos Git Útiles

```bash
# Ver estado
git status

# Ver cambios
git diff

# Ver historial
git log --oneline

# Agregar cambios
git add .              # Todo
git add archivo.py     # Archivo específico

# Comitear
git commit -m "mensaje descriptivo"

# Subir a GitHub
git push

# Bajar cambios (si trabajas en múltiples máquinas)
git pull

# Crear rama para features
git checkout -b feature/nueva-funcionalidad
git push -u origin feature/nueva-funcionalidad
```

---

## .gitignore (Recomendado)

Ya incluye:
- `.env` (credenciales)
- `__pycache__/`
- `*.pyc`
- `node_modules/` (si usas React)
- `.pytest_cache/`
- Archivos del IDE

---

## Estructura Final en GitHub

Después de subir, verás en GitHub:

```
telegram_antifraud/
├── README.md ✅
├── COMPLETION_SUMMARY.md ✅
├── requirements.txt ✅
├── docker-compose.yml ✅
├── docker-compose.full.yml ✅ (NUEVO)
├── .env.example ✅
├── Dockerfile ✅
│
├── bots/
│   ├── public_bot.py ✅
│   ├── private_bot.py ✅
│   └── userbot.py ✅
│
├── engine/
│   ├── worker.py ✅
│   ├── scoring.py ✅
│   ├── clusters.py ✅
│   ├── honeypot.py ✅
│   ├── raid.py ✅
│   ├── rules.py ✅
│   ├── shadow_mod.py ✅
│   ├── logger.py ✅
│   └── ab_testing.py ✅ (NUEVO)
│
├── db/
│   └── models.py ✅
│
├── api/
│   └── dashboard.py ✅
│
├── tools/
│   ├── traffic_simulator.py ✅
│   ├── userbot_opsec.py ✅
│   └── pagerduty_integration.py ✅ (NUEVO)
│
├── frontend/ ✅ (NUEVA)
│   ├── package.json
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   └── Navigation.js
│   │   └── pages/
│   │       ├── Dashboard.js
│   │       ├── Users.js
│   │       ├── Rules.js
│   │       ├── AuditLog.js
│   │       └── Alerts.js
│
├── monitoring/ ✅ (NUEVA)
│   ├── prometheus.yml
│   ├── alert-rules.yml
│   ├── alertmanager.yml
│   ├── grafana-datasources.yml
│   └── grafana-dashboard-antifraud.json
│
├── docs/
│   ├── MODERATION_POLICY.md ✅
│   ├── TOS_CHECKLIST.md ✅
│   ├── PRIVACY_POLICY.md ✅
│   ├── SECURITY_POLICY.md ✅
│   ├── OPERATIONS_MANUAL.md ✅
│   ├── SCALABILITY.md ✅
│   └── SOC2_COMPLIANCE_ROADMAP.md ✅ (NUEVO)
│
├── tests/
│   └── test_advanced.py ✅
│
├── examples/
│   ├── logging.py ✅
│   └── metrics.py ✅
│
├── rules.json ✅
├── demo.py ✅
├── config.py ✅
└── .gitignore ✅
```

---

## Pasos Resumen (Rápido)

```bash
# 1. Ir al directorio
cd C:\workspace\telegram_antifraud

# 2. Iniciar git si no lo tiene
git init

# 3. Configurar usuario (primera vez)
git config --global user.name "hasbulla"
git config --global user.email "hasbulla@example.com"

# 4. Agregar todos los archivos
git add -A

# 5. Primer commit
git commit -m "Initial commit: Complete antifraud system with 5 new features"

# 6. Conectar a GitHub
git remote add origin https://github.com/YOUR_USERNAME/telegram_antifraud.git

# 7. Cambiar a rama main
git branch -M main

# 8. **SUBIR A GITHUB** 🚀
git push -u origin main

# 9. Verificar
git log --oneline
# https://github.com/YOUR_USERNAME/telegram_antifraud
```

---

## Troubleshooting

**Error: fatal: not a git repository**
```bash
git init
```

**Error: remote origin already exists**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/telegram_antifraud.git
```

**Error: permission denied (publickey)**
- Usa HTTPS en lugar de SSH
- O configura SSH key [Guía SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

**Error: fatal: The current branch main has no upstream branch**
```bash
git push -u origin main
```

---

## Post-Upload: Configuración en GitHub

1. **Ir a Settings → Branches**
   - Set `main` como default branch
   - Habilitar "Require pull request reviews"

2. **Ir a Actions**
   - Habilitar GitHub Actions para CI/CD

3. **Ir a Security & Analysis**
   - Dependabot alerts
   - Code scanning

4. **Ir a Insights → Traffic**
   - Ver descargas, clonaciones, etc

---

**¡Listo! Tu proyecto está en GitHub! 🎉**

Ahora otros pueden:
```bash
git clone https://github.com/YOUR_USERNAME/telegram_antifraud.git
cd telegram_antifraud
docker-compose up -d
```
