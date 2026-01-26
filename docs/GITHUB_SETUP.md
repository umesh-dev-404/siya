# GITHUB SETUP & PI DEPLOYMENT GUIDE
## Project: Siya
## Purpose: Push code to GitHub and deploy to Raspberry Pi

---

## OVERVIEW

This guide walks you through:
1. Setting up a GitHub repository
2. Pushing Siya code to GitHub
3. Cloning and deploying on Raspberry Pi

---

## STEP 1: INITIALIZE GIT REPOSITORY (PC)

### 1.1 Initialize Git

```bash
# Navigate to project directory
cd d:\Projects\siya

# Initialize git repository
git init

# Set default branch name (optional, if not already set globally)
git branch -M main
```

### 1.2 Configure Git (if not already done)

```bash
# Set your name and email (replace with your GitHub credentials)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Or set globally
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 1.3 Stage All Files

```bash
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status
```

### 1.4 Create Initial Commit

```bash
# Create first commit
git commit -m "Initial commit: Siya v1.0.0-baseline

- Phase 0-3, 5-9 complete
- Production baseline ready
- Network access configured
- All core systems implemented"
```

---

## STEP 2: CREATE GITHUB REPOSITORY

### 2.1 Create Repository on GitHub

1. **Go to GitHub:** https://github.com/new
2. **Repository name:** `siya` (or your preferred name)
3. **Description:** "Local-First Personal Governance and Assistant Operating System"
4. **Visibility:** 
   - **Private** (recommended for personal projects)
   - **Public** (if you want to share)
5. **DO NOT** initialize with:
   - ❌ README
   - ❌ .gitignore
   - ❌ license
   (We already have these)
6. **Click "Create repository"**

### 2.2 Copy Repository URL

After creating, GitHub will show you the repository URL:
- **HTTPS:** `https://github.com/YOUR_USERNAME/siya.git`
- **SSH:** `git@github.com:YOUR_USERNAME/siya.git`

**Note:** Use HTTPS if you haven't set up SSH keys, or SSH if you have.

---

## STEP 3: PUSH TO GITHUB (PC)

### 3.1 Add Remote Repository

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/siya.git

# Or if using SSH:
# git remote add origin git@github.com:YOUR_USERNAME/siya.git

# Verify remote
git remote -v
```

### 3.2 Push to GitHub

```bash
# Push to main branch
git push -u origin main
```

**If prompted for credentials:**
- **HTTPS:** Use GitHub username and Personal Access Token (not password)
- **SSH:** Should work automatically if keys are set up

### 3.3 Create Release Tag (Optional but Recommended)

```bash
# Tag the baseline version
git tag -a v1.0.0-baseline -m "Siya v1.0.0-baseline - Production baseline"

# Push tags to GitHub
git push origin v1.0.0-baseline
```

---

## STEP 4: CLONE ON RASPBERRY PI

### 4.1 SSH into Pi

```bash
# From your PC
ssh YOUR_PI_USERNAME@raspberrypi  # Replace YOUR_PI_USERNAME with your actual Pi username (e.g., umesh404)
# Or use IP: ssh YOUR_PI_USERNAME@192.168.1.XXX
```

### 4.2 Install Git (if not installed)

```bash
# On Pi
sudo apt update
sudo apt install -y git
```

### 4.3 Clone Repository

```bash
# Navigate to installation directory
cd /opt

# Clone repository (replace YOUR_USERNAME)
sudo git clone https://github.com/YOUR_USERNAME/siya.git

# Or if using SSH:
# sudo git clone git@github.com:YOUR_USERNAME/siya.git

# Set ownership
sudo chown -R YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya  # Replace YOUR_PI_USERNAME with your actual Pi username (e.g., umesh404)
```

### 4.4 Verify Clone

```bash
cd /opt/siya
ls -la
git log --oneline -5
```

---

## STEP 5: SET UP ON PI

### 5.1 Follow Deployment Guide

Continue with `docs/DEPLOYMENT.md` from Step 2 (System Hardening) onwards:

```bash
cd /opt/siya

# Read deployment guide
cat docs/DEPLOYMENT.md
```

### 5.2 Quick Setup Commands

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# Initialize database
python -c "from memory.database import MemoryDatabase; db = MemoryDatabase(); db.initialize()"

# Configure network access
export SIYA_API_HOST=0.0.0.0
export SIYA_WEB_HOST=0.0.0.0
export SIYA_API_BASE_URL=http://$(hostname -I | awk '{print $1}'):8080
```

---

## STEP 6: VERIFY DEPLOYMENT

### 6.1 Check Services

```bash
# On Pi, test API
curl http://localhost:8080/health

# Find Pi IP
hostname -I
```

### 6.2 Access from PC

```bash
# From PC, replace <PI_IP> with actual IP
curl http://<PI_IP>:8080/health

# Open web interface in browser
# http://<PI_IP>:3000
```

---

## TROUBLESHOOTING

### Git Push Issues

**Authentication Failed:**
- Use Personal Access Token instead of password
- Generate token: GitHub → Settings → Developer settings → Personal access tokens
- Or set up SSH keys

**Repository Not Found:**
- Check repository name and username
- Verify you have push access

### Pi Clone Issues

**Permission Denied:**
```bash
# Fix ownership
sudo chown -R YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya  # Replace YOUR_PI_USERNAME with your actual Pi username (e.g., umesh404)
```

**Git Not Found:**
```bash
sudo apt update && sudo apt install -y git
```

**Network Issues:**
- Ensure Pi has internet access
- Check firewall settings
- Try HTTPS instead of SSH (or vice versa)

---

## ONGOING DEVELOPMENT WORKFLOW

### Making Changes (PC)

```bash
# Make changes to code
# ...

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

### Updating Pi

```bash
# SSH into Pi
ssh YOUR_PI_USERNAME@raspberrypi  # Replace YOUR_PI_USERNAME with your actual Pi username

# Navigate to project
cd /opt/siya

# Pull latest changes
git pull origin main

# Restart services if needed
sudo systemctl restart siya
```

---

## SECURITY NOTES

### GitHub Repository

- **Private repository recommended** for personal projects
- **Never commit:**
  - `.env` files
  - `production_lock.json` (runtime file)
  - Database files (`*.db`)
  - Secrets or API keys

### Pi Deployment

- Use SSH keys for GitHub (more secure than HTTPS tokens)
- Keep Pi updated: `sudo apt update && sudo apt upgrade`
- Configure firewall: `sudo ufw enable`

---

## NEXT STEPS

After successful deployment:

1. ✅ Code pushed to GitHub
2. ✅ Code cloned on Pi
3. ⏭️ Follow `docs/DEPLOYMENT.md` for full Pi setup
4. ⏭️ Configure systemd service (see DEPLOYMENT.md)
5. ⏭️ Test network access from PC (see NETWORK_ACCESS.md)

---

**Last Updated:** 2026-01-26  
**Status:** Ready for GitHub setup
