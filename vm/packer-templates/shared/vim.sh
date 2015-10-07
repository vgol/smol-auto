#!/bin/bash

pack="vim-vgolcfg_0.1.4_all.deb"
url="ftp://192.168.32.160/packages/"

wget ${url}$pack
if [[ $? == 0 ]]; then
    dpkg -i $pack
fi
