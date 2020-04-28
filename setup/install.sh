#!/usr/bin/env bash

DISTRO=`grep "^ID=" /etc/os-release | cut -d\= -f2`

# https://stackoverflow.com/questions/3349105/how-to-set-current-working-directory-to-the-directory-of-the-script
cd "${0%/*}"

if [[ $EUID -ne 0 ]]; then
   echo " [!]This script must be run as root" 1>&2
   exit 1
fi

if [ ! -f ../config.ini ]; then
    cp config_default.ini ../config.ini
fi

# https://stackoverflow.com/questions/4023830/how-to-compare-two-strings-in-dot-separated-version-format-in-bash
verlte() {
    [  "$1" = "`echo -e "$1\n$2" | sort -V | head -n1`" ]
}

verlt() {
    [ "$1" = "$2" ] && return 1 || verlte $1 $2
}

echo ""
echo "*************************************************"
echo "*        Installing applications via apt        *"
echo "*************************************************"
echo ""


if [ "$1" == "-d" ]; then
    INSTALL_DOCKER="true"
fi


if [ "$DISTRO" == "kali" ]; then

    apt-get update -y
    if [[ $? > 0 ]]; then
        echo
        echo
        echo "[!] apt-get update failed, exiting..."
        exit
    fi
    if [ "$INSTALL_DOCKER" == "true" ]; then
        apt-get install curl gnupg2 -y
        curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
        echo 'deb [arch=amd64] https://download.docker.com/linux/debian buster stable' > /etc/apt/sources.list.d/docker.list
        apt-get update -y
        apt-get remove docker docker-engine docker.io containerd runc -y
        apt-get install apt-transport-https ca-certificates curl wget gnupg2 software-properties-common docker-ce vim curl gobuster nikto cewl whatweb sqlmap nmap sslscan sslyze hydra medusa dnsrecon enum4linux ncrack crowbar onesixtyone smbclient redis-server seclists chromium python-pip python3-pip wpscan jq amass -y
    else
        apt-get update -y
        apt-get install apt-transport-https ca-certificates curl wget gnupg2 software-properties-common vim curl gobuster nikto cewl whatweb sqlmap nmap sslscan sslyze hydra medusa dnsrecon enum4linux ncrack crowbar onesixtyone smbclient redis-server seclists chromium python-pip python3-pip wpscan jq amass -y

    fi
elif [ "$DISTRO" == "ubuntu" ]; then
    apt-get update -y
    if [[ $? > 0 ]]; then
        echo
        echo
        echo "[!]  apt-get update failed, exiting..."
        exit
    fi
   if [ "$INSTALL_DOCKER" == "true" ]; then
        apt-get install curl gnupg2 -y
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" -y
        apt-get update -y
        apt-get install wget docker.io python-pip python3-pip unzip redis-server chromium-bsu jq -y
    else
        apt-get update -y
        apt-get install wget curl vim python-pip python3-pip unzip redis-server chromium-bsu jq -y

    fi
fi


CELERYSTALK_DIR=`pwd`

echo ""
echo "**************************************"
echo "*      Starting redis-server          *"
echo "**************************************"
echo ""
IS_PORT_CONFIGURED=`grep "^port 6379" /etc/redis/redis.conf`
if [ $? == "1" ]; then
    echo "port 6379" >> /etc/redis/redis.conf
fi
sed -i.bak '/^bind/s/::1//g' /etc/redis/redis.conf
/etc/init.d/redis-server start

echo ""
echo "******************************************"
echo "* Installing celerystalk python requirements via pip *"
echo "******************************************"
echo ""
pip2 install -r requirements.txt --upgrade


echo ""
echo "**************************************"
echo "*      Starting python-libnessus     *"
echo "**************************************"
echo ""

if [ ! -f /opt/python-libnessus/python_libnessus.egg-info ]; then
    cd /opt/
    git clone https://github.com/bmx0r/python-libnessus.git
    cd python-libnessus
    python setup.py install
fi

if [ "$DISTRO" == "ubuntu" ]; then
    if [ ! -f /opt/amass/amass ]; then
        echo ""
        echo "****************************************"
        echo "* Installing Amass to /opt/amass/amass *"
        echo "****************************************"
        echo ""
        mkdir -p /opt/amass
        wget https://github.com/OWASP/Amass/releases/download/3.0.3/amass_3.0.3_linux_i386.zip -O /opt/amass/amass_3.0.3_linux_i386.zip
        unzip /opt/amass/amass_3.0.3_linux_i386.zip -d /opt/amass
        mv /opt/amass/amass_3.0.3_linux_i386/* /opt/amass/
    fi
fi

if [ ! -f /opt/aquatone/aquatone ]; then
    echo ""
    echo "*******************************************************"
    echo "* Installing Aquatone to /opt/aquatone/aquatone       *"
    echo "*******************************************************"
    echo ""
    echo "[+] Downloading Aquatone to /opt/aquatone/aquatone"
    mkdir -p /opt/aquatone
    wget https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /opt/aquatone/aquatone_linux_amd64_1.7.0.zip
    unzip -o /opt/aquatone/aquatone_linux_amd64_1.7.0.zip -d /opt/aquatone
else
    CURRENT_VERSION=`/opt/aquatone/aquatone -version | cut -dv -f2`
    DESIRED_MINIMUM_VERSION="1.7.0"
    IS_LESS_THAN_DESIRED=`verlt $CURRENT_VERSION $DESIRED_MINIMUM_VERSION`

    if [ $? == "0" ]; then
        echo ""
        echo "**********************************************"
        echo "*           Updating Aquatone                *"
        echo "**********************************************"
        echo ""
        cd /opt/aquatone
        wget https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /opt/aquatone/aquatone_linux_amd64_1.7.0.zip
        unzip -o /opt/aquatone/aquatone_linux_amd64_1.7.0.zip -d /opt/aquatone
    fi
fi


if [ ! -f /opt/Sublist3r/sublist3r.py ]; then
    echo ""
    echo "*******************************************************"
    echo "* Installing sublist3r to /opt/Sublist3r/sublist3r.py *"
    echo "*******************************************************"
    echo ""

    cd /opt/
    git clone https://github.com/aboul3la/Sublist3r.git
    cd Sublist3r/
    pip install -r requirements.txt
else
    echo ""
    echo "**********************************************"
    echo "*           Updating sublist3r               *"
    echo "**********************************************"
    echo ""
    cd /opt/Sublist3r/
    git pull
    pip install -r requirements.txt
fi

if [ ! -f /opt/Photon/photon.py ]; then
    echo ""
    echo "**********************************************"
    echo "* Installing Photon to /opt/Photon/photon.py *"
    echo "**********************************************"
    echo ""
    cd /opt/
    git clone https://github.com/s0md3v/Photon.git
    cd Photon
    pip3 install -r requirements.txt
else
    echo ""
    echo "**********************************************"
    echo "*           Updating Photon                  *"
    echo "**********************************************"
    echo ""
    cd /opt/Photon
    git pull
    pip3 install -r requirements.txt
fi

echo ""
echo "**********************************************"
echo "*           Installing ssh-audit             *"
echo "**********************************************"
echo ""
pip3 install ssh-audit



#if [ ! -f /opt/CMSmap/cmsmap.py ]; then
#    echo ""
#    echo "**********************************************"
#    echo "* Installing CMSmap to /opt/CMSmap/cmsmap.py *"
#    echo "**********************************************"
#    echo ""
#    cd /opt/
#    git clone https://github.com/Dionach/CMSmap.git
#    cd CMSmap
#    pip3 install .
#    echo "y" | cmsmap -U P
#else
#    echo ""
#    echo "**********************************************"
#    echo "*           Updating CMSmap                  *"
#    echo "**********************************************"
#    echo ""
#    cd /opt/CMSmap
#    git pull
#    pip3 install .
#    echo "y" | cmsmap -U P
#fi

cd $CELERYSTALK_DIR
cp bash_completion_file /etc/bash_completion.d/celerystalk.sh
cd .. && ./celerystalk -h

echo ""
echo "[+]"
echo "[+] To use the fancy bash completion right away, copy/paste the following (you'll only need to do this once):"
echo "[+]   . /etc/bash_completion.d/celerystalk.sh"