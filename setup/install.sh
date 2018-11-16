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
    apt install gobuster redis-server seclists firefox-esr xvfb python3-pip wpscan jq -y
elif [ "$DISTRO" == "ubuntu" ]; then
    echo "ubuntu"
    apt install python-pip python3-pip unzip redis-server firefox xvfb jq -y
fi

CELERYSTALK_DIR=`pwd`

echo "[+] Starting redis-server"
/etc/init.d/redis-server start
echo "[+] Installing python requirements via pip"
pip install -r requirements.txt --upgrade


if [ ! -f /usr/bin/geckodriver ]; then
    #From: https://github.com/FortyNorthSecurity/EyeWitness/blob/master/setup/setup.sh
    MACHINE_TYPE=`uname -m`
    if [ ${MACHINE_TYPE} == 'x86_64' ]; then
      wget https://github.com/mozilla/geckodriver/releases/download/v0.22.0/geckodriver-v0.22.0-linux64.tar.gz
      tar -xvf geckodriver-v0.22.0-linux64.tar.gz
      rm geckodriver-v0.22.0-linux64.tar.gz
      mv geckodriver /usr/sbin
      ln -s /usr/sbin/geckodriver /usr/bin/geckodriver
    else
      wget https://github.com/mozilla/geckodriver/releases/download/v0.22.0/geckodriver-v0.22.0-linux32.tar.gz
      tar -xvf geckodriver-v0.22.0-linux32.tar.gz
      rm geckodriver-v0.22.0-linux64.tar.gz
      mv geckodriver /usr/sbin
      ln -s /usr/sbin/geckodriver /usr/bin/geckodriver
    fi


    # https://gist.github.com/cgoldberg/4097efbfeb40adf698a7d05e75e0ff51#file-geckodriver-install-sh
    install_dir="/usr/bin"
    json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
    if [[ $(uname) == "Linux" ]]; then
        url=$(echo "$json" | jq -r '.assets[].browser_download_url | select(contains("linux64"))')
        echo $url
    else
        echo "can't determine OS"
        exit 1
    fi
    curl -s -L "$url" | tar -xz
    chmod +x geckodriver
    mv geckodriver "$install_dir"
    echo "installed geckodriver binary in $install_dir"
fi


if [ ! -f /opt/amass/amass ]; then
    echo "[+] Downloading OWASP Amass to /opt/amass/amass"
    mkdir -p /opt/amass
    wget https://github.com/OWASP/Amass/releases/download/v2.5.0/amass_2.5.2_linux_386.zip -O /opt/amass/amass_2.5.2_linux_386.zip
    unzip /opt/amass/amass_2.5.2_linux_386.zip -d /opt/amass
fi

if [ ! -f /opt/Sublist3r/sublist3r.py ]; then
    echo "[+] Downloading sublist3r to /opt/Sublist3r"
    cd /opt/
    git clone https://github.com/aboul3la/Sublist3r.git
    cd Sublist3r/
    pip install -r requirements.txt
else
    cd /opt/Sublist3r/
    git pull
    pip install -r requirements.txt
fi

if [ ! -f /opt/Photon/photon.py ]; then
    echo "[+] Downloading Photon Web Spider to /opt/Photon/photon.py"
    cd /opt/
    git clone https://github.com/s0md3v/Photon.git
    cd Photon
    pip install -r requirements.txt
else
    cd /opt/Photon
    git pull
    pip install -r requirements.txt
fi

if [ ! -f /opt/CMSmap/cmsmap.py ]; then
    echo "[+] Downloading CMSMap to /opt/CMSmap/cmsmap.py"
    cd /opt/
    git clone https://github.com/Dionach/CMSmap.git
    cd CMSmap
    pip3 install .
    cmsmap -U P
else
    cd /opt/CMSmap
    git pull
    pip3 install .
    cmsmap -U P
fi

cd $CELERYSTALK_DIR
cp bash_completion_file /etc/bash_completion.d/celerystalk.sh
../celerystalk -h
echo ""
echo "[+] Back up a directory and you are ready to go."
echo ""
echo "[+] To use the fancy bash completion right away, copy/paste the following (you'll only need to do this once):"
echo "[+]   . /etc/bash_completion.d/celerystalk.sh"

