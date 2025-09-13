# Vulnerability Scanning Platform (OpenVAS/GVM) — Complete Solution

A complete web-based vulnerability scanning platform that integrates with OpenVAS/GVM (Greenbone Vulnerability Management) running in Docker. This project provides a simple, task wizard-like interface for running vulnerability scans.

## 🎯 Project Overview

This platform consists of:
- **Frontend**: Clean HTML/CSS/JS interface (no frameworks required)
- **Backend**: FastAPI server that communicates with OpenVAS via GMP API
- **Scanner**: OpenVAS/GVM running in Docker container
- **Deployment**: Web application runs on Ubuntu VM alongside OpenVAS
- **Workflow**: Enter IP → Auto-create target → Auto-create task → Run scan → Get results

## 🏗️ Architecture

```
┌───────────────────┐    HTTP     ┌───────────────────┐    GMP API    ┌───────────────────┐
│   HTML Frontend   │ ─────────→ │  FastAPI Backend  │ ─────────→   │  OpenVAS Docker   │
│   (index.html)    │             │   (backend.py)    │               │   (port 9390)     │
└───────────────────┘             └───────────────────┘               └───────────────────┘
         ↑                                ↑                                ↑
         │                                │                                │
    Nginx (port 80)                Ubuntu VM                        Ubuntu VM
```

**Important**: The entire web application (frontend + backend) runs on the Ubuntu VM where OpenVAS is located. This is required for network scanning to work properly.

## 🚀 Features

- ✅ **Simple Interface**: Just enter an IP address and click "Start Scan"
- ✅ **Network Scanning**: Choose between single IP or network range (CIDR) scanning
- ✅ **Real OpenVAS Integration**: Uses actual OpenVAS scans, not mock data
- ✅ **Automatic Target/Task Creation**: Like OpenVAS task wizard
- ✅ **Real-time Progress Monitoring**: Watch scan status updates
- ✅ **Complete Results**: Get actual vulnerability findings
- ✅ **Docker-based**: Easy deployment with OpenVAS container
- ✅ **Scan History Persistence**: Scans are saved in your browser (localStorage). Refreshing the page keeps your scan list and status updates.
- ✅ **Authentication (No Sign-Up)**: Token-based sign-in; admin can create users

## 📋 Prerequisites

- Ubuntu VM with Docker
- Python 3.10+
- Nmap (for network scanning)
- Git
 - Nginx (reverse proxy) — optional but recommended

## ⚙️ Installation & Setup

### Quick Setup on Ubuntu VM
1. **Run the setup script**:
   ```bash
   chmod +x setup-ubuntu-vm.sh
   ./setup-ubuntu-vm.sh
   ```

2. **Copy project files** to `/home/$USER/scan-app/`

3. **Start OpenVAS container**:
   ```bash
   docker run -d -p 9390:9390 -p 9392:9392 --name openvas immauss/openvas:22.4.51
   ```

4. **Access the web app** at `http://your-vm-ip`

### Manual Setup
Follow the steps in `me-to-do.txt` and `backend-setup-instructions.txt` for detailed manual installation.

## 🔐 Authentication & Users

### Sign-In (No Sign-Up)
- Visit `/login.html` to sign in. On success, you are redirected to `/` and a token is stored in your browser.
- All API calls require a Bearer token. The frontend handles this automatically after login.

### Default Users (seeded automatically)
- `admin` / `admin123` (admin)
- `univ1` / `univ1pass`
- `univ2` / `univ2pass`

You can override passwords with environment variables when starting the backend:
```bash
export ADMIN_PASSWORD='StrongAdminPass'
export UNIV1_PASSWORD='StrongPass1'
export UNIV2_PASSWORD='StrongPass2'
export TOKEN_SECRET='change_me_to_random_secret'
export TOKEN_TTL_MIN=720
python3 backend.py
```

### Admin User Creation
- Admins can create users at `/admin.html` or via API `POST /admin/users` with JSON body `{ "username": "...", "password": "...", "is_admin": false }`.

## 🎮 How to Use

### 1. Access the Web Interface
- Open your browser and go to: `http://your-ubuntu-vm-ip`
- The web interface will be served by nginx

### 2. Sign In
- Go to `/login.html` and sign in with one of the seeded users.

### 3. Test the Connection
- Optionally enable the test button in `script.js` to verify OpenVAS connectivity

### 4. Run a Scan
- Choose scan type from dropdown:
  - **Single IP Address**: Enter an IP (e.g., `192.168.1.1`)
  - **Network Range**: Enter a CIDR range (e.g., `192.168.200.0/24`)
- Enter your email for PDF reports
- Click "Start Scan"
- Watch the real-time progress and results!

### 5. Network Scanning Workflow
When you select "Network Range":
1. Enter a CIDR range (e.g., `192.168.200.0/24`)
2. The system will first scan the network with Nmap to find live hosts
3. All live hosts will be added to a single OpenVAS target
4. One scan task will be created for the entire network
5. Results will include vulnerabilities for all hosts in the network

**Note:** The backend is stateless. If you restart the backend server, it will not remember previous scans. The frontend will still show your scans and try to update their status, but may show errors if the backend cannot find them.

## 📁 Project Structure

```
/home/user/scan-app/
├── index.html                    # Main frontend interface
├── style.css                     # Frontend styling
├── script.js                     # Frontend logic (real scans)
├── backend.py                    # FastAPI backend (real OpenVAS)
├── setup-ubuntu-vm.sh           # Ubuntu VM setup script
├── me-to-do.txt                  # Detailed setup checklist
├── backend-setup-instructions.txt # Backend setup guide
└── README.md                     # This file
```

## 🔧 Configuration

### OpenVAS Connection Settings
In `backend.py`:
```python
OPENVAS_HOST = 'localhost'    # OpenVAS Docker container (same VM)
OPENVAS_PORT = 9390          # GMP API port
OPENVAS_USER = 'admin'       # Default username
OPENVAS_PASS = 'admin'       # Default password
```

### Web Server Configuration
- **Nginx**: Serves frontend on port 80
- **Backend**: Runs on port 8000 (proxied by nginx at `/api`)
- **Systemd Service**: `scan-backend.service` manages the backend

### Auth Environment Variables
- `TOKEN_SECRET`: HMAC secret for tokens (change in production)
- `TOKEN_TTL_MIN`: Token lifetime in minutes (default 720)
- `ADMIN_PASSWORD`, `UNIV1_PASSWORD`, `UNIV2_PASSWORD`: Seeded passwords

## 🔍 API Endpoints

- `GET /` - Backend status
- `POST /auth/login` - Sign in (returns token)
- `GET /me` - Current user info (requires Authorization)
- `POST /admin/users` - Create user (admin only)
- `GET /test-connection` - Test OpenVAS connectivity
- `GET /nmap-scan?ip_range=...` - Scan network for live hosts
- `POST /scan` - Start a new scan (requires `target` IP/network and `scan_type`)
- `GET /scan-status/{task_id}` - Check scan progress
- `GET /scan-results/{task_id}` - Get completed scan results

## 🐞 Troubleshooting

### Common Issues

1. **"Failed to connect to OpenVAS"**
   - Check if Docker container is running: `docker ps`
   - Verify port 9390 is exposed: `nc -vz localhost 9390`

2. **"Authentication failed"**
   - Default credentials are `admin/admin`
   - Check OpenVAS container logs: `docker logs openvas`

3. **"Network scan timeout"**
   - Network scans can take 5-30 minutes depending on network size
   - Check scan status via OpenVAS web interface: `http://localhost:9392`

4. **"Web app not accessible"**
   - Check nginx status: `sudo systemctl status nginx`
   - Check backend status: `sudo systemctl status scan-backend`
   - View logs: `sudo journalctl -u scan-backend -f`

### Debug Commands
```bash
# Check OpenVAS container status
docker ps | grep openvas

# View OpenVAS logs
docker logs openvas

# Check backend service
sudo systemctl status scan-backend

# View backend logs
sudo journalctl -u scan-backend -f

# Test GMP connection manually
python test_gvm_connection.py
```

## 🔒 Security Notes

- This is designed for **lab/development environments**
- Default OpenVAS credentials are used (`admin/admin`)
- For production, change passwords, set `TOKEN_SECRET`, and restrict access
- The web app runs on the same VM as OpenVAS for network access

## 🚀 Next Steps

- [ ] Add scan scheduling capabilities
- [ ] Implement scan result export (PDF, CSV)
- [x] Add user authentication
- [ ] Create scan templates for different use cases
- [ ] Add email notifications for completed scans

## 🧰 Ubuntu Setup (Detailed)

The commands below assume a fresh Ubuntu 22.04+ VM with sudo privileges.

### 1) Install system dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nmap nginx docker.io git
sudo systemctl enable --now docker
```

### 2) Clone project and set up Python environment
```bash
mkdir -p ~/scan-app && cd ~/scan-app
cp -r /workspace/* .  # or git clone your repo here
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn[standard] gvm-tools python-nmap anyio typing-extensions
```

If `gvm` Python package is required by your environment, also install:
```bash
pip install python-gvm
```

### 3) Run OpenVAS (GVM) in Docker
```bash
sudo docker run -d \
  -p 9390:9390 -p 9392:9392 \
  --name openvas immauss/openvas:22.4.51
```

Update `OPENVAS_HOST` in `backend.py` if OpenVAS is on a different host.

### 4) Configure environment and start backend
```bash
cd ~/scan-app
source .venv/bin/activate
export TOKEN_SECRET="$(openssl rand -hex 32)"
export ADMIN_PASSWORD='admin123'
export UNIV1_PASSWORD='univ1pass'
export UNIV2_PASSWORD='univ2pass'
python3 backend.py
```

Backend starts on `http://0.0.0.0:8000`. It seeds users and protects all API routes.

### 5) Serve frontend via Nginx with /api proxy
Create an Nginx site config (example):
```bash
sudo tee /etc/nginx/sites-available/scan-app <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    root /home/$USER/scan-app;
    index index.html login.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/scan-app /etc/nginx/sites-enabled/scan-app
sudo nginx -t && sudo systemctl restart nginx
```

Then browse to `http://<VM-IP>/login.html`.

### 6) Optional: Run backend as a systemd service
```bash
sudo tee /etc/systemd/system/scan-backend.service <<'UNIT'
[Unit]
Description=Scan App Backend (FastAPI)
After=network.target

[Service]
User=%i
WorkingDirectory=/home/%i/scan-app
Environment=TOKEN_SECRET=change_me
Environment=ADMIN_PASSWORD=admin123
Environment=UNIV1_PASSWORD=univ1pass
Environment=UNIV2_PASSWORD=univ2pass
ExecStart=/home/%i/scan-app/.venv/bin/python3 /home/%i/scan-app/backend.py
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable scan-backend
sudo systemctl start scan-backend
```

Check logs:
```bash
sudo journalctl -u scan-backend -f
```

## 📄 License

MIT License - Feel free to use and modify for your needs.

---

**🎉 You now have a complete, working vulnerability scanner that integrates with real OpenVAS scans and can scan networks!**

---

**Note:**
- For step-by-step setup and troubleshooting, see `me-to-do.txt` and `backend-setup-instructions.txt` in this repository.
- The web application must run on the Ubuntu VM for network scanning to work properly.