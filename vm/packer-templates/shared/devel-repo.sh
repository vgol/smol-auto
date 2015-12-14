#!/bin/bash

url="http://192.168.32.160/unstable/smolensk/mounted-iso-devel" 
echo "deb $url smolensk main non-free contrib" >> /etc/apt/sources.list

apt-get -y update
apt-get clean
