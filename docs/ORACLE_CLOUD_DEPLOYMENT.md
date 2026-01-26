# NSE Scraper — Oracle Cloud Always Free Runbook

This is the operational runbook for deploying and running this repo on Oracle Cloud Always Free with MongoDB Atlas (free tier).

## Deployment profiles

Choose one:

1) Micro VM (1 OCPU / ~1GB RAM)
- Use: `docker-compose.lite.yml` + `Dockerfile.lite`
- No Chrome/Selenium required (cookie acquisition is HTTP-based; Selenium is disabled in lite)

2) Larger VM (optional)
- Use: `docker-compose.prod.yml`

## What runs where

- FastAPI server: `http://<VM_PUBLIC_IP>:1020`
  - Health: `/health`
  - Swagger UI: `/docs`
- Schedulers (cron jobs): runs inside the same container process (see `Services/cron_jobs.py`)
- Database: MongoDB Atlas (recommended for $0/month)

---

## 1) MongoDB Atlas (free tier)

1. Create an M0 cluster.
2. Create a DB user (save username/password).
3. Network Access: allow your VM IP. For quick testing you can temporarily allow `0.0.0.0/0`.
4. Copy the SRV connection string.

### Important: `%` escaping in `config.ini`

This repo reads `config.ini` with Python `configparser`, which treats `%` specially.

If your password contains special characters:
- First URL-encode the password in the URI (example: `@` becomes `%40`).
- Then, when you paste the URI into `config.ini`, escape every `%` as `%%`.

Example:
- URI encoding needs `%40`
- In `config.ini` you must write `%%40`

---

## 2) Oracle Cloud VM setup

### Required ports

Allow these inbound:
- `22/tcp` for SSH
- `1020/tcp` for the API (direct access, optional if using Nginx)
- `80/tcp` for Nginx + Let’s Encrypt HTTP challenge
- `443/tcp` for HTTPS

You must allow them in:
- Oracle VCN Security List / NSG rules
- VM firewall (Ubuntu `ufw`) if enabled

### Connect from Windows (PowerShell)

```powershell
ssh -i C:\path\to\your\private-key.key ubuntu@<VM_PUBLIC_IP>
```

---

## 2.1) Domain setup (recommended: `api.jaychauhan.tech`)

Since `jaychauhan.tech` is already used for your portfolio (Render), host this project on a subdomain.

1. Create a DNS **A record**:
   - Name/Host: `api`
   - Value: `<YOUR_ORACLE_VM_PUBLIC_IP>`
   - TTL: default

2. Wait for DNS to propagate.

From your machine:

```powershell
nslookup api.jaychauhan.tech
```

---

## 2.2) Nginx reverse proxy + HTTPS (Let’s Encrypt)

Goal:
- API base URL: `https://api.jaychauhan.tech`

Nginx will terminate TLS and proxy to the container at `http://127.0.0.1:1020`.

### Install Nginx

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Create Nginx site

```bash
sudo nano /etc/nginx/sites-available/stockmarket-api
```

Paste:

```nginx
server {
  listen 80;
  server_name api.jaychauhan.tech;

  location / {
    proxy_pass http://127.0.0.1:1020;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
  }
}
```

Enable the site:

```bash
sudo ln -sf /etc/nginx/sites-available/stockmarket-api /etc/nginx/sites-enabled/stockmarket-api
sudo nginx -t
sudo systemctl reload nginx
```

### Install Certbot (HTTPS)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.jaychauhan.tech
```

Verify:

```bash
curl -sS https://api.jaychauhan.tech/health
```

Swagger:
- `https://api.jaychauhan.tech/docs`

### Auto-renew check

```bash
sudo certbot renew --dry-run
```

---

## 2.3) Important security notes (recommended)

### Prefer not exposing `1020` publicly

Once Nginx is working, restrict direct access to port `1020`:
- Oracle Security List / NSG: remove inbound `1020/tcp`
- Keep only `80/tcp` and `443/tcp` public

### UFW (Ubuntu firewall)

If you use `ufw`:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 3) Install Docker (Ubuntu)

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Log out and log back in after changing groups.

---

## 4) Deploy (micro VM / lite)

### 4.1 Clone

```bash
git clone <YOUR_REPO_URL>
cd NSE-Scraper
```

### 4.2 Configure `config.ini`

`docker-compose.lite.yml` mounts `./config.ini` into the container.

At minimum set:
- MongoDB Atlas URIs
- Any project-specific toggles you need (intervals, force-run, etc.)

### 4.3 Start

```bash
docker compose -f docker-compose.lite.yml up -d --build
```

### 4.4 Verify

On the VM:

```bash
curl -sS http://localhost:1020/health
```

From your machine:
- `http://<VM_PUBLIC_IP>:1020/health`
- `http://<VM_PUBLIC_IP>:1020/docs`

---

## 5) Operations

### View container status

```bash
docker compose -f docker-compose.lite.yml ps
docker stats
```

### Follow logs

```bash
docker compose -f docker-compose.lite.yml logs -f --tail=200
```

### App file logs

The repo writes file logs under `Logs/` (mounted from host).

```bash
ls -la Logs
tail -f Logs/*.log
```

### Restart / stop

```bash
docker compose -f docker-compose.lite.yml restart
docker compose -f docker-compose.lite.yml down
```

### Update to latest code

```bash
git pull
docker compose -f docker-compose.lite.yml up -d --build
```

---

## 6) Cron jobs: how to confirm they run

Cron scheduling is implemented in `Services/cron_jobs.py`.

How to verify:
- Check container logs for periodic job start/finish messages.
- Check MongoDB collections update (most scrapers do delete-then-insert).

### Market-hours gating

By default, jobs may run only during market hours (IST weekdays 9:15–15:30).

If you need to test outside market hours, enable the project’s force-run flag (if present in your `config.ini`, as implemented in `Services/cron_jobs.py`) and restart the container.

---

## 7) Manual refresh APIs

Swagger UI:
- `http://<VM_PUBLIC_IP>:1020/docs`

Common endpoints:
- NSE refresh: `POST /nse/refresh/all` and per-source refresh endpoints under `/nse/refresh/...`
- IPO refresh: `POST /ipo/refresh/investorgain`, `POST /ipo/refresh/match-zerodha`, `POST /ipo/refresh/all`

---

## 8) Cookies (no copy/paste)

Cookie acquisition is handled in `Services/get_nse_cookies.py`.

Lite deployment notes:
- Selenium is disabled via env (`USE_SELENIUM=false`).
- The server fetches NSE cookies using an HTTP-based flow and caches them.
- The cache file is `nse_cookies.json` in the repo root (mounted into the container).

If you see repeated 401/403 from NSE:
- Confirm the VM’s IP isn’t blocked.
- Confirm time zone is IST (`TZ=Asia/Kolkata`).
- Review headers logic in `Utils/cookie_headers.py`.

---

## 9) Troubleshooting

### API not reachable publicly

1. On the VM: `curl http://localhost:1020/health`
2. Ensure Oracle ingress allows `1020/tcp`.
3. If `ufw` is enabled:
   - `sudo ufw allow 1020/tcp`
   - `sudo ufw status`

### MongoDB Atlas connection fails

- Confirm Atlas IP access list allows the VM.
- Confirm `config.ini` has correct escaping (`%` must be `%%`).

### Swagger “Failed to fetch”

Use `http://<VM_PUBLIC_IP>:1020/docs` (not `localhost`). The OpenAPI server is configured to be relative so Swagger targets the same host.

---

## 10) Codebase map

- `main.py`: entrypoint (starts API + cron)
- `Loader/server.py`: FastAPI app, router registration, `/health`, OpenAPI config
- `Services/cron_jobs.py`: schedule definitions + job runners
- `Services/get_nse_cookies.py`: NSE cookie acquisition + caching
- `API/Controller/`: each scraper controller (request → format → DB)
- `API/Router/`: FastAPI routes (including manual refresh endpoints)
- `Utils/data_formatter.py`: transforms NSE JSON into Mongo-ready docs
- `Utils/db.py`: MongoDB access patterns (collections, delete-then-insert)
- `Constant/`: URLs and shared constants

---

## Appendix: prod compose (larger VM)

If you later move to a bigger VM:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

