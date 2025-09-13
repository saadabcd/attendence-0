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

## 📋 Prerequisites

- Ubuntu VM with Docker
- Python 3.8+
- Nmap (for network scanning)
- Git

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

## 🎮 How to Use

### 1. Access the Web Interface
- Open your browser and go to: `http://your-ubuntu-vm-ip`
- The web interface will be served by nginx

### 2. Test the Connection
- Click "Test Connection" to verify OpenVAS connectivity
- You should see the OpenVAS version if connection is successful

### 3. Run a Scan
- Choose scan type from dropdown:
  - **Single IP Address**: Enter an IP (e.g., `192.168.1.1`)
  - **Network Range**: Enter a CIDR range (e.g., `192.168.200.0/24`)
- Enter your email for PDF reports
- Click "Start Scan"
- Watch the real-time progress and results!

### 4. Network Scanning Workflow
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
- **Backend**: Runs on port 8000 (proxied by nginx)
- **Systemd Service**: `scan-backend.service` manages the backend

## 🔍 API Endpoints

- `GET /` - Backend status
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
- For production, change passwords and restrict access
- The web app runs on the same VM as OpenVAS for network access

## 🚀 Next Steps

- [ ] Add scan scheduling capabilities
- [ ] Implement scan result export (PDF, CSV)
- [ ] Add user authentication
- [ ] Create scan templates for different use cases
- [ ] Add email notifications for completed scans

## 📄 License

MIT License - Feel free to use and modify for your needs.

---

**🎉 You now have a complete, working vulnerability scanner that integrates with real OpenVAS scans and can scan networks!**

---

**Note:**
- For step-by-step setup and troubleshooting, see `me-to-do.txt` and `backend-setup-instructions.txt` in this repository.
- The web application must run on the Ubuntu VM for network scanning to work properly.