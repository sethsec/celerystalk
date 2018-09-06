#!/usr/bin/env bash

DISTRO=`grep "^ID=" /etc/os-release | cut -d\= -f2`

if [[ $EUID -ne 0 ]]; then
   echo " [!]This script must be run as root" 1>&2
   exit 1
fi

if [ ! -f config.ini ]; then
    cp config_default.ini ../config.ini
    echo "[+] Copied config.ini.repo to config.ini"
fi
echo "[+] Updating apt sources"
apt update -y

echo "[+] Installing redis-server, gobuster, seclists"
if [ "$DISTRO" == "kali" ]; then
    echo "kali"
    apt install gobuster redis-server seclists chromium chromium-driver -y
elif [ "$DISTRO" == "ubuntu" ]; then
    echo "ubuntu"
    apt install redis-server chromium-chromedriver -y
    ln -s /usr/lib/chromium-browser/chromedriver /usr/bin/chromedriver
fi

CELERYSTALK_DIR=`pwd`

echo "[+] Starting redis-server"
/etc/init.d/redis-server start
echo "[+] Installing python requirements via pip"
pip install -r requirements.txt

if [ ! -f /opt/amass/amass ]; then
    echo "[+] Downloading OWASP Amass to /opt/amass/amass"
    mkdir -p /opt/amass
    wget https://github.com/OWASP/Amass/releases/download/v2.4.0/amass_2.4.2_linux_386.zip -O /opt/amass/amass_2.4.2_linux_386.zip
    unzip /opt/amass/amass_2.4.2_linux_386.zip -d /opt/amass
fi

if [ ! -f /opt/Sublist3r/sublist3r.py ]; then
    echo "[+] Downloading sublist3r to /opt/Sublist3r"
    cd /opt/
    git clone https://github.com/aboul3la/Sublist3r.git
    cd Sublist3r/
    pip install -r requirements.txt
fi

if [ ! -f /opt/Photon/photon.py ]; then
    echo "[+] Downloading Photon Web Spider to /opt/Photon/photon.py"
    cd /opt/
    git clone https://github.com/s0md3v/Photon.git
    cd Photon
    pip install -r requirements.txt
fi

cd $CELERYSTALK_DIR
cp bash_completion_file /etc/bash_completion.d/celerystalk.sh
../celerystalk -h
echo ""
echo "[+] Back up a directory and you are ready to go."
echo ""
echo "[+] To use the fancy bash completion right away, copy/paste the following (you'll only need to do this once):"
echo "[+]   . /etc/bash_completion.d/celerystalk.sh"

