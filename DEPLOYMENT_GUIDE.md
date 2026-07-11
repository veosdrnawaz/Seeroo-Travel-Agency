# Seeroo Travels Attock — Deployment Guide

> **Phase 7: Production Hardening & Deployment Readiness**
> This guide covers everything needed to run the Seeroo Travels API in a production environment.

---

## Table of Contents

1. [Required Environment Variables](#1-required-environment-variables)
2. [PostgreSQL Setup](#2-postgresql-setup)
3. [Redis Setup](#3-redis-setup)
4. [Gmail App Password (SMTP)](#4-gmail-app-password-smtp)
5. [Running with Uvicorn (Development)](#5-running-with-uvicorn-development)
6. [Running with Gunicorn (Production)](#6-running-with-gunicorn-production)
7. [Nginx Reverse Proxy](#7-nginx-reverse-proxy)
8. [SSL with Let's Encrypt](#8-ssl-with-lets-encrypt)
9. [Environment Modes Reference](#9-environment-modes-reference)
10. [API Route Reference](#10-api-route-reference)

---

## 1. Required Environment Variables

Copy `.env.example` (or your `.env`) and fill in all values before starting the server.

### Development (minimum required)

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./seeroo_travels.db
OPENAI_API_KEY=sk-...          # Optional in dev (MockChatModel fallback active)
SMTP_USER=                     # Optional in dev
SMTP_PASS=                     # Optional in dev
```

### Production (all required)

```env
ENVIRONMENT=production

# Database — PostgreSQL required
DATABASE_URL=postgresql://seeroo_user:StrongPassword123@localhost:5432/seeroo_travels_db

# Server
HOST=0.0.0.0
PORT=8000

# CORS — comma-separated allowed origins
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# OpenAI — REQUIRED, startup fails without it
OPENAI_API_KEY=sk-proj-...

# SMTP — REQUIRED in production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx   # 16-char App Password

# Redis — REQUIRED in production
REDIS_URL=redis://localhost:6379/0

# Request limits
MAX_REQUEST_SIZE_BYTES=1048576   # 1 MB
REQUEST_TIMEOUT_SECONDS=30

# Logging
LOG_LEVEL=WARNING
LOG_JSON=true
```

> **Note**: In `production` mode the server performs fail-fast checks at startup and will exit immediately if any of the above required values are missing.

---

## 2. PostgreSQL Setup

### Install PostgreSQL (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

### Create the database and user

```bash
sudo -u postgres psql << 'EOF'
CREATE USER seeroo_user WITH PASSWORD 'StrongPassword123';
CREATE DATABASE seeroo_travels_db OWNER seeroo_user;
GRANT ALL PRIVILEGES ON DATABASE seeroo_travels_db TO seeroo_user;
EOF
```

### Install the Python PostgreSQL driver

```bash
pip install psycopg2-binary
```

> Uncomment `# psycopg2-binary` in `requirements.txt` before deploying.

### Update `.env`

```env
DATABASE_URL=postgresql://seeroo_user:StrongPassword123@localhost:5432/seeroo_travels_db
```

### Run Alembic migrations

```bash
python -m alembic upgrade head
```

> The application is backward-compatible with SQLite for development. PostgreSQL is the **recommended production database**.

---

## 3. Redis Setup

Redis is used in production for:
- **Sliding-window rate limiting** (replaces in-memory store, survives restarts).
- **LangGraph agent memory checkpoints** (replaces SQLite checkpointer).

### Install Redis (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping   # should return PONG
```

### Install LangGraph Redis checkpointer

```bash
pip install langgraph-checkpoint-redis
```

> Then uncomment `# langgraph-checkpoint-redis` in `requirements.txt`.

### Configure Redis with a password (recommended)

```bash
sudo nano /etc/redis/redis.conf
# Add or modify:
requirepass YourRedisPassword
```

```bash
sudo systemctl restart redis-server
```

Update `.env`:

```env
REDIS_URL=redis://:YourRedisPassword@localhost:6379/0
```

---

## 4. Gmail App Password (SMTP)

The email system uses Gmail SMTP with STARTTLS (port 587). A standard Gmail password will not work — you must generate a 16-character **App Password**.

### Steps

1. Sign in to your Google Account.
2. Go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Select **App**: `Mail` → **Device**: `Other (Custom name)` → type `Seeroo Travels`.
4. Click **Generate**.
5. Copy the 16-character password (spaces included are fine).

### Update `.env`

```env
SMTP_USER=youraddress@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
```

> **Security**: Never commit `.env` to version control. Add `.env` to `.gitignore`.

---

## 5. Running with Uvicorn (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server (auto-reload on file changes)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Access the API docs
# http://localhost:8000/api/v1/docs

# Access the frontend
# http://localhost:8000/index.html

# Health check
# http://localhost:8000/api/v1/health
```

---

## 6. Running with Gunicorn (Production)

Gunicorn provides multi-worker process management. Use it with Uvicorn workers for async FastAPI support.

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Start with 4 Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level warning
```

### Recommended worker count formula

```
workers = (2 × CPU_cores) + 1
```

For a 2-core VPS: `workers = 5`.

### Systemd service (auto-restart on crashes)

Create `/etc/systemd/system/seeroo.service`:

```ini
[Unit]
Description=Seeroo Travels Attock API
After=network.target redis.service postgresql.service

[Service]
User=www-data
WorkingDirectory=/var/www/seeroo-travels
EnvironmentFile=/var/www/seeroo-travels/.env
ExecStart=/usr/local/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/tmp/seeroo.sock \
    --timeout 60
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable seeroo
sudo systemctl start seeroo
sudo systemctl status seeroo
```

---

## 7. Nginx Reverse Proxy

Nginx acts as the public-facing web server, forwarding requests to Gunicorn.

### Install Nginx

```bash
sudo apt install -y nginx
```

### Create site configuration

`/etc/nginx/sites-available/seeroo`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Request size limit (matches backend setting)
    client_max_body_size 2M;

    # Proxy to Gunicorn Unix socket
    location / {
        proxy_pass http://unix:/tmp/seeroo.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
    }

    # Static assets — serve directly via Nginx for performance
    location ~* \.(css|js|png|jpg|webp|svg|ico|woff2)$ {
        root /var/www/seeroo-travels;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/seeroo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 8. SSL with Let's Encrypt

### Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Issue certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically:
1. Obtain a free SSL certificate from Let's Encrypt.
2. Configure Nginx to redirect HTTP → HTTPS.
3. Schedule automatic renewal via cron/systemd.

### Verify auto-renewal

```bash
sudo certbot renew --dry-run
```

---

## 9. Environment Modes Reference

| Feature                     | `development`               | `production`                       |
|-----------------------------|-----------------------------|------------------------------------|
| MockChatModel fallback      | ✅ Allowed                  | ❌ Blocked (startup fails)          |
| Empty SMTP credentials      | ✅ Allowed (email skipped)  | ❌ Blocked (startup fails)          |
| Empty REDIS_URL             | ✅ SQLite fallback active   | ❌ Blocked (startup fails)          |
| Empty OPENAI_API_KEY        | ✅ MockChatModel used       | ❌ Blocked (startup fails)          |
| CORS policy                 | Wildcard `*`               | Strict `CORS_ORIGINS` list          |
| Log format                  | Coloured human-readable     | JSON Lines (machine-readable)       |
| Log level default           | `INFO`                     | `WARNING`                          |
| SQLite checkpointer         | ✅ Default                  | Redis (SQLite fallback if no Redis) |
| Rate limiter                | In-memory (per-process)     | Redis (distributed, survives restart)|

---

## 10. API Route Reference

All API routes are versioned under the `/api/v1/` prefix.

| Method | Path                            | Description                     |
|--------|---------------------------------|---------------------------------|
| GET    | `/api/v1/health`                | Dependency health probes        |
| GET    | `/api/v1/docs`                  | Swagger UI                      |
| GET    | `/api/v1/tours`                 | List all tours                  |
| GET    | `/api/v1/tours/{id}`            | Get tour details by ID          |
| POST   | `/api/v1/tours`                 | Create new tour (admin)         |
| POST   | `/api/v1/bookings`              | Create booking                  |
| GET    | `/api/v1/bookings/{id}`         | Get booking invoice by ID       |
| POST   | `/api/v1/chat`                  | AI agent conversation endpoint  |
| GET    | `/`                             | Static frontend (index.html)    |

---

*Last updated: 2026-07-11 | Phase 7: Production Hardening*
