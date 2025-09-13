#!/bin/bash

# Setup script for deploying the vulnerability scanner web app on Ubuntu VM
# This script sets up the complete environment on the Ubuntu VM

echo "Setting up vulnerability scanner web app on Ubuntu VM..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx nmap git docker.io
sudo systemctl enable --now docker

# Create project directory
echo "Setting up project directory..."
mkdir -p /home/$USER/scan-app
cd /home/$USER/scan-app

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install fastapi "uvicorn[standard]" python-gvm python-nmap anyio typing_extensions

# Optionally run OpenVAS container if not running
if ! sudo docker ps --format '{{.Names}}' | grep -q '^openvas$'; then
  echo "Starting OpenVAS container..."
  sudo docker run -d -p 9390:9390 -p 9392:9392 --name openvas immauss/openvas:22.4.51 || true
fi

# Create systemd service for the backend
echo "Creating systemd service for backend..."
sudo tee /etc/systemd/system/scan-backend.service > /dev/null <<EOF
[Unit]
Description=Vulnerability Scanner Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/scan-app
Environment=TOKEN_SECRET=change_me
Environment=ADMIN_PASSWORD=admin123
Environment=UNIV1_PASSWORD=univ1pass
Environment=UNIV2_PASSWORD=univ2pass
ExecStart=/home/$USER/scan-app/venv/bin/python3 /home/$USER/scan-app/backend.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the backend service
sudo systemctl daemon-reload
sudo systemctl enable scan-backend
sudo systemctl start scan-backend

# Configure nginx
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/scan-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Serve static files (frontend)
    location / {
        root /home/$USER/scan-app;
        index index.html login.html;
        try_files \$uri \$uri/ =404;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the nginx site
sudo ln -sf /etc/nginx/sites-available/scan-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Set proper permissions
sudo chown -R $USER:$USER /home/$USER/scan-app

# Fix permissions for nginx to access the files
echo "Setting proper permissions for nginx..."
sudo chmod 755 /home/$USER/
sudo chmod -R a+rX /home/$USER/scan-app

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy project files into /home/$USER/scan-app (index.html, login.html, admin.html, backend.py, style.css, script.js)"
echo "2. If OpenVAS is not running, start it: sudo docker start openvas"
echo "3. Access the web app at: http://$(hostname -I | awk '{print $1}')/login.html"
echo "4. Check backend status: sudo systemctl status scan-backend"
echo "5. Check nginx status: sudo systemctl status nginx"
echo ""
echo "To view logs:"
echo "  Backend: sudo journalctl -u scan-backend -f"
echo "  Nginx: sudo tail -f /var/log/nginx/access.log" 