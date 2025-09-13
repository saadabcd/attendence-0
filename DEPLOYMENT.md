# Deployment Guide - Ubuntu VM Setup

This guide explains how to deploy the vulnerability scanner web application on the Ubuntu VM where OpenVAS is running.

## 🎯 Why Ubuntu VM Deployment is Required

The web application **must** run on the Ubuntu VM (not Windows) because:

1. **Network Access**: Only the Ubuntu VM can access the target network via VPN
2. **Nmap Scanning**: Network discovery requires direct access to the target network
3. **OpenVAS Integration**: Direct communication with OpenVAS container

## 🚀 Quick Deployment

### Step 1: Transfer Files to Ubuntu VM
```bash
# From your Windows machine, copy files to Ubuntu VM
scp -r /path/to/scan-page user@192.168.1.38:/home/user/scan-app
```

### Step 2: Run Setup Script
```bash
# On Ubuntu VM
cd /home/user/scan-app
chmod +x setup-ubuntu-vm.sh
./setup-ubuntu-vm.sh
```

### Step 3: Start OpenVAS Container
```bash
# Make sure OpenVAS is running
docker run -d -p 9390:9390 -p 9392:9392 --name openvas immauss/openvas:22.4.51
```

### Step 4: Access Web Application
- Open browser and go to: `http://192.168.1.38`
- The web interface will be served by nginx

## 🔧 Manual Deployment

If you prefer manual setup:

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx nmap git
```

### 2. Set Up Python Environment
```bash
cd /home/$USER/scan-app
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-gvm python-nmap
```

### 3. Configure Nginx
```bash
sudo tee /etc/nginx/sites-available/scan-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        root /home/$USER/scan-app;
        index index.html;
        try_files \$uri \$uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/scan-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Create Systemd Service
```bash
sudo tee /etc/systemd/system/scan-backend.service > /dev/null <<EOF
[Unit]
Description=Vulnerability Scanner Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/scan-app
Environment=PATH=/home/$USER/scan-app/venv/bin
ExecStart=/home/$USER/scan-app/venv/bin/uvicorn backend:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable scan-backend
sudo systemctl start scan-backend
```

## 🔍 Verification

### Check Services
```bash
# Check backend service
sudo systemctl status scan-backend

# Check nginx service
sudo systemctl status nginx

# Check OpenVAS container
docker ps | grep openvas
```

### Test Connectivity
```bash
# Test backend API
curl http://localhost:8000/

# Test nginx proxy
curl http://localhost/api/

# Test OpenVAS connection
curl http://localhost/api/test-connection
```

### View Logs
```bash
# Backend logs
sudo journalctl -u scan-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# OpenVAS logs
docker logs openvas
```

## 🐞 Troubleshooting

### Common Issues

1. **"Permission denied"**
   ```bash
   sudo chown -R $USER:$USER /home/$USER/scan-app
   ```

2. **"Port already in use"**
   ```bash
   sudo netstat -tulpn | grep :8000
   sudo pkill -f uvicorn
   ```

3. **"Nginx configuration error"**
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **"Backend not starting"**
   ```bash
   sudo journalctl -u scan-backend -f
   cd /home/$USER/scan-app && source venv/bin/activate && python backend.py
   ```

### Network Configuration

Make sure your Ubuntu VM has:
- **VPN connection** to the target network
- **Port forwarding** for HTTP (port 80) if accessing from outside
- **Firewall rules** allowing HTTP traffic

## 🔒 Security Considerations

1. **Change default passwords** in production
2. **Use HTTPS** for production deployments
3. **Restrict access** to the web interface
4. **Regular updates** of system packages

## 📊 Monitoring

### System Resources
```bash
# Check CPU and memory usage
htop

# Check disk space
df -h

# Check network connections
netstat -tulpn
```

### Application Health
```bash
# Check all services
sudo systemctl status scan-backend nginx docker

# Test web interface
curl -I http://localhost/
```

---

**🎉 Your vulnerability scanner is now deployed and ready to scan networks!** 