#!/bin/bash
# Install python3-all, python3-pytest and python3-pexpec.
# The former required build from source package.

list="
python-all
python3-all
python3-setuptools 
dh-python
python-sphinx
debhelper
"
url="ftp://192.168.32.160/packages"
pexpect_url="${url}/pexpect"
pytest_url="${url}/pytest"
py_version="1.4.31"
pytest_version="2.8.4"
pexpect_version="3.3"


apt-get -y install $list
apt-get clean


# pexpect
easy_install3 ${pexpect_url}/pexpect-${pexpect_version}.tar.gz

# pytest
easy_install3 ${pytest_url}/py-${py_version}.tar.gz
easy_install3 ${pytest_url}/pytest-${pytest_version}.tar.gz
