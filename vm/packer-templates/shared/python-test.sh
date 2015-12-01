#!/bin/bash
# Install python3-all, python3-pytest and python3-pexpec.
# The former required build from source package.

list="
python-all
python3-all
python3-pytest 
dh-python
python-sphinx
debhelper
"
url="ftp://192.168.32.160/packages/pexpect"
srcdir="/root/pexpect"


apt-get -y install $list
apt-get clean


wget -r -nH --cut-dirs=1 -P /root $url
wait

curdir=$PWD
cd $srcdir
dpkg-source -x pexpect_*.dsc
cd pexpect-*
dpkg-buildpackage -us -uc
wait
dpkg -i ../python3-pexpect*.deb
cd $curdir
rm -r $srcdir
