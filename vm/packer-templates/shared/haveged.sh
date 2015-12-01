#!/bin/bash
# Get and build haveged (enthropy generator).

list="dh-autoreconf dh-systemd"
url="ftp://192.168.32.160/packages/haveged"
srcdir="/root/haveged"


apt-get -y install $list
apt-get clean

wget -r -nH --cut-dirs=1 -P /root $url
wait

curdir=$PWD
cd $srcdir
dpkg-source -x haveged_*.dsc
cd haveged-*
dpkg-buildpackage -us -uc
wait
dpkg -i ../libhavege1_*.deb ../haveged_*.deb
cd $curdir
rm -r $srcdir
