#!/bin/bash

# Step 1: Check if we're in the right directory (hospicesys)
if [ ! -d "hospicesys" ]; then
    echo "Error: Directory hospicesys not found. Please ensure you're in the correct directory."
    exit 1
fi

# Step 2: Update apt repositories and install all necessary packages
echo "Updating apt repositories and installing necessary packages..."
sudo apt update
sudo apt install -y apache2 python3-pip python3-venv libapache2-mod-wsgi-py3

# Step 3: Check python version
echo "Checking python version..."
python3 --version

# Step 4: Create a virtual environment (if not already created)
if [ ! -d "env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv env
fi
source env/bin/activate

# Step 5: Install packages from requirements.txt
echo "Installing required packages from requirements.txt..."
pip3 install -r requirements.txt

# Step 6: Apache Server Configurations
echo "Configuring Apache virtual host..."

# Create the Apache config file (hospicesys.conf)
cat <<EOL | sudo tee /etc/apache2/sites-available/hospicesys.conf
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    ServerName example.com
    ServerAlias www.example.com
    DocumentRoot /home/ubuntu/hospicesys
    <Directory /home/ubuntu/hospicesys>
        AllowOverride all
        Require all granted
        Options FollowSymlinks
        Allow from all
    </Directory>

    Alias /media /home/ubuntu/hospicesys/media
    Alias /static /home/ubuntu/hospicesys/static

    <Directory /home/ubuntu/hospicesys/static>
        Require all granted
    </Directory>

    <Directory /home/ubuntu/hospicesys/media>
        Require all granted
    </Directory>

    <Directory /home/ubuntu/hospicesys/hospicesys>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    WSGIDaemonProcess hospicesys python-path=/home/ubuntu/hospicesys python-home=/home/ubuntu/hospicesys/env
    WSGIProcessGroup hospicesys
    WSGIScriptAlias / /home/ubuntu/hospicesys/hospicesys/wsgi.py
</VirtualHost>
EOL

# Step 7: Enable Apache site configuration and install mod_wsgi
echo "Enabling Apache site configuration..."
sudo a2ensite hospicesys.conf
sudo a2dissite 000-default.conf
sudo a2enmod wsgi

# Step 8: Start Apache if it's not already running
echo "Starting Apache service..."
sudo service apache2 start

# Step 9: Reload Apache (less disruptive than restart)
echo "Reloading Apache to apply changes..."
sudo service apache2 reload

echo "Deployment complete!"
