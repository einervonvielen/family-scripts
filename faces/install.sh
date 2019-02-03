#!/bin/bash
# run as root
#   - Debian: "su -" then "install.sh"
#   - Ubuntu: "sudo install.sh"
#
# 2017-09-30
# Tested under Debian9
#
echo "Install python3 and pip..."
apt-get install -y cmake curl libboost-all-dev python3-setuptools python3 python3-pip
#Install face_recognition (which installs dlib as well)
echo "Install face_recognition..."
pip3 install face_recognition
echo "install exiftool and ufraw-batch..."
apt-get -y install libimage-exiftool-perl ufraw-batch
