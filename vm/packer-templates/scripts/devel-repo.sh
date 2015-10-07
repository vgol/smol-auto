echo 'deb ftp://192.168.32.160/astra/unstable/smolensk/mounted-iso-devel/ smolensk main non-free contrib'  >> /etc/apt/sources.list

apt-get -y update
apt-get clean
