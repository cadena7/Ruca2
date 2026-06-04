
#!/bin/bash
################################################################################
# Script for Basic Raspian Default Apps
# Author: Edgar Cadena
#-------------------------------------------------------------------------------
# Make a new file:
# sudo nano raspi.sh
# sudo chmod +x raspi.sh
# Execute the script:
# ./raspidefault
################################################################################

sudo apt-get update && sudo apt-get upgrade -y && sudo apt-get dist-upgrade -y


sudo apt-get install git python3 python3-dev python3-setuptools python3-pip -y


sudo pip3 install pip --upgrade
sudo pip3 install rpi.gpio greenlet eventlet gevent sqlalchemy flask Flask-Excel Flask-SQLAlchemy gunicorn Adafruit-GPIO

sudo apt-get install nginx supervisor python3-flask nmap net-tools htop ufw fail2ban -y

sudo ufw default allow outgoing
sudo ufw default deny incoming

sudo ufw allow ssh/tcp
sudo ufw logging on
sudo ufw allow 80/tcp
sudo ufw allow http/tcp
sudo ufw allow https
sudo ufw allow ftp
sudo ufw allow ntp

sudo ufw allow 8000
sudo ufw allow 5555
sudo ufw allow 6666
sudo ufw allow 7777
sudo ufw allow 9001
sudo ufw allow 1880
sudo ufw allow 5900
sudo ufw allow 1883

sudo ufw limit ssh/tcp

sudo ufw enable
sudo ufw status

echo "DONE"
