# NSE Scraper - Oracle Cloud Free Tier Deployment Guide

## 🆓 Complete Free Hosting Setup

This guide covers hosting the NSE Scraper with **$0/month** cost using:
- **Oracle Cloud Always Free VM** - 24GB RAM ARM instance (lifetime free)
- **MongoDB Atlas Free Tier** - 512MB cloud database (lifetime free)
- **Docker** - Container deployment for easy management

---

## 📋 Prerequisites

1. **Oracle Cloud Account** - Sign up at [cloud.oracle.com](https://cloud.oracle.com)
2. **MongoDB Atlas Account** - Sign up at [mongodb.com/atlas](https://www.mongodb.com/atlas)
3. **Basic Linux knowledge** - SSH, terminal commands

---

## 🗄️ Step 1: Setup MongoDB Atlas (Free Tier)

### 1.1 Create MongoDB Atlas Account
1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Sign up with email or Google account
3. Choose **FREE** tier (M0 Sandbox)

### 1.2 Create Free Cluster
1. Click **"Build a Database"**
2. Select **M0 FREE** tier (512MB storage, shared RAM)
3. Choose provider: **AWS** or **GCP** (closest region to India for low latency)
4. Cluster name: `nse-scraper-cluster`
5. Click **Create Cluster** (takes 3-5 minutes)

### 1.3 Configure Database Access
1. Go to **Database Access** → **Add New Database User**
2. Authentication: Password
   - Username: `nse_scraper_user`
   - Password: Generate a strong password (save it!)
3. Database User Privileges: **Read and write to any database**
4. Click **Add User**

### 1.4 Configure Network Access
1. Go to **Network Access** → **Add IP Address**
2. For initial setup: Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - Later, restrict to your Oracle Cloud VM IP for security
3. Click **Confirm**

### 1.5 Get Connection String
1. Go to **Database** → Click **Connect**
2. Choose **"Connect your application"**
3. Driver: Python, Version: 3.12 or later
4. Copy the connection string:
   ```
   mongodb+srv://nse_scraper_user:<password>@nse-scraper-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password

---

## ☁️ Step 2: Setup Oracle Cloud Free VM

### 2.1 Create Oracle Cloud Account
1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Sign up for **Free Tier** (requires credit card for verification, won't be charged)
3. Choose home region closest to you (Mumbai for India)

### 2.2 Create Always Free VM Instance
1. Go to **Compute** → **Instances** → **Create Instance**

2. **Name**: `nse-scraper-server`

3. **Image and Shape**:
   - Click **Edit**
   - Image: **Oracle Linux 8** or **Ubuntu 22.04**
   - Shape: Click **Change Shape**
     - Instance type: **Ampere** (ARM)
     - Shape: **VM.Standard.A1.Flex** ⭐ (Always Free)
     - OCPUs: **4** (max free)
     - Memory: **24 GB** (max free)
   
4. **Networking**:
   - Create new VCN or use existing
   - Assign public IPv4 address: **Yes**

5. **Add SSH Keys**:
   - Generate key pair or paste your public key
   - **IMPORTANT**: Download private key and save securely!

6. Click **Create** (takes 2-5 minutes)

### 2.3 Configure Security Rules (Firewall)
1. Go to **Networking** → **Virtual Cloud Networks**
2. Click your VCN → **Security Lists** → Default Security List
3. Add **Ingress Rules**:

| Stateless | Source | Protocol | Dest Port | Description |
|-----------|--------|----------|-----------|-------------|
| No | 0.0.0.0/0 | TCP | 22 | SSH |
| No | 0.0.0.0/0 | TCP | 1020 | FastAPI Server |
| No | 0.0.0.0/0 | TCP | 80 | HTTP (optional) |
| No | 0.0.0.0/0 | TCP | 443 | HTTPS (optional) |

### 2.4 Connect to VM via SSH
```bash
# Linux/Mac
ssh -i /path/to/private-key.key ubuntu@<YOUR_VM_PUBLIC_IP>

# Windows (PowerShell)
ssh -i C:\path\to\private-key.key ubuntu@<YOUR_VM_PUBLIC_IP>

# Windows (using PuTTY)
# Convert .key to .ppk using PuTTYgen, then connect
```

---

## 🐳 Step 3: Install Docker on Oracle Cloud VM

### 3.1 Connect to VM and Update System
```bash
# SSH into your VM
ssh -i your-key.key ubuntu@<VM_IP>

# Update system
sudo apt update && sudo apt upgrade -y
```

### 3.2 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Logout and login again for group changes
exit
# SSH back in
```

### 3.3 Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 📦 Step 4: Deploy NSE Scraper

### 4.1 Clone Repository
```bash
cd ~
git clone https://github.com/anv-het/NSE-Scraper.git
cd NSE-Scraper
```

### 4.2 Create Production Configuration
```bash
# Copy and edit config
cp config.ini config.production.ini
nano config.production.ini
```

Update these values in `config.production.ini`:
```ini
[DATABASE]
MONGO_URI = mongodb+srv://nse_scraper_user:YOUR_PASSWORD@nse-scraper-cluster.xxxxx.mongodb.net/
MONGO_DB = NSE_SCRAPER
MONGO_DB_MASTER = GETMASTERDATA

# Disable SQL Server if not needed
SQL_SERVER_ENABLED = false

[SCRAPING]
DATA_COLLECTION_INTERVAL = 5
TIMEOUT = 30
COOKIE_REFRESH_INTERVAL = 60

[SERVER]
HOST = 0.0.0.0
PORT = 1020
DEBUG = false
```

### 4.3 Deploy with Docker Compose
```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4.4 Verify Deployment
```bash
# Check if API is running
curl http://localhost:1020/health

# Check from outside (use your VM's public IP)
curl http://<YOUR_VM_PUBLIC_IP>:1020/health
```

---

## 🔧 Step 5: Configure Systemd Service (Auto-start)

Create a systemd service so the scraper starts automatically on boot:

```bash
sudo nano /etc/systemd/system/nse-scraper.service
```

Add this content:
```ini
[Unit]
Description=NSE Scraper Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/NSE-Scraper
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable nse-scraper
sudo systemctl start nse-scraper
```

---

## 🔒 Step 6: Security Best Practices

### 6.1 Configure Firewall on VM
```bash
# Allow only necessary ports
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 1020 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Save iptables rules
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

### 6.2 Restrict MongoDB Atlas Access
After deployment, go to MongoDB Atlas:
1. **Network Access** → Remove 0.0.0.0/0
2. Add only your Oracle Cloud VM's public IP

### 6.3 Setup HTTPS with Nginx (Optional but Recommended)
```bash
# Install Nginx
sudo apt install nginx -y

# Install Certbot for free SSL
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com
```

---

## 📊 Step 7: Monitoring & Maintenance

### 7.1 Check Application Status
```bash
# Container status
docker-compose -f docker-compose.prod.yml ps

# Application logs
docker-compose -f docker-compose.prod.yml logs -f nse-scraper

# Resource usage
docker stats
```

### 7.2 MongoDB Atlas Monitoring
1. Go to Atlas Dashboard → **Metrics**
2. Monitor: Storage usage, Connections, Operations/sec
3. Set up **Alerts** for storage approaching limit

### 7.3 Useful Commands
```bash
# Restart application
docker-compose -f docker-compose.prod.yml restart

# Update application
cd ~/NSE-Scraper
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# View cron job logs
docker-compose -f docker-compose.prod.yml logs -f | grep -i cron

# Check disk space
df -h
```

---

## 💰 Cost Summary

| Service | Tier | Cost | Limits |
|---------|------|------|--------|
| Oracle Cloud VM | Always Free | **$0/month** | 4 OCPUs, 24GB RAM, 200GB storage |
| MongoDB Atlas | M0 Free | **$0/month** | 512MB storage, shared RAM |
| Domain (optional) | Freenom/.tk | **$0/year** | Free domains available |
| SSL Certificate | Let's Encrypt | **$0/year** | Auto-renew with Certbot |

**Total Monthly Cost: $0** 🎉

---

## ⚠️ Free Tier Limitations

### Oracle Cloud Always Free
- ✅ **No expiration** - truly lifetime free
- ⚠️ Must use ARM (Ampere) instances for 24GB RAM
- ⚠️ Idle instances may be reclaimed (keep active with cron jobs)
- ⚠️ 10TB/month outbound data transfer

### MongoDB Atlas Free Tier
- ✅ **No expiration** - lifetime free
- ⚠️ 512MB storage limit
- ⚠️ Shared cluster (may have slower performance)
- ⚠️ No backups on free tier

### Preventing Oracle VM Reclamation
Oracle may reclaim idle Always Free instances. Keep it active:
```bash
# Add to crontab to keep VM active
crontab -e

# Add this line (runs every hour)
0 * * * * curl -s http://localhost:1020/health > /dev/null
```

---

## 🚀 Quick Start Commands

```bash
# 1. SSH to VM
ssh -i key.pem ubuntu@<VM_IP>

# 2. Clone and setup
git clone https://github.com/anv-het/NSE-Scraper.git
cd NSE-Scraper

# 3. Configure
cp config.ini config.production.ini
nano config.production.ini  # Update MongoDB URI

# 4. Deploy
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Verify
curl http://localhost:1020/health
```

---

## 📞 Troubleshooting

### Cannot connect to VM
```bash
# Check if VM is running in Oracle Console
# Verify security list rules allow port 22
# Check if correct private key is used
```

### API not accessible from outside
```bash
# Check iptables
sudo iptables -L

# Check if container is running
docker ps

# Check Oracle Security List for port 1020
```

### MongoDB connection failed
```bash
# Test connection
python -c "from pymongo import MongoClient; c = MongoClient('YOUR_URI'); print(c.list_database_names())"

# Check Atlas Network Access includes VM IP
# Verify username/password in connection string
```

### Container keeps restarting
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs nse-scraper

# Check if Chrome/Chromedriver works in container
docker exec -it nse-scraper bash
python -c "from Services.get_nse_cookies import get_nse_cookies; print(get_nse_cookies())"
```

---

## 📁 File Structure for Deployment

```
NSE-Scraper/
├── Dockerfile                    # Docker build instructions
├── docker-compose.prod.yml       # Production compose file
├── config.production.ini         # Production configuration
├── .dockerignore                 # Files to exclude from Docker
├── scripts/
│   ├── deploy.sh                 # Deployment script
│   └── health_check.sh           # Health monitoring script
└── ...
```

---

**Next Steps:**
1. Create Oracle Cloud account
2. Setup MongoDB Atlas free cluster
3. Launch Oracle VM
4. Deploy using this guide

Happy Hosting! 🚀
