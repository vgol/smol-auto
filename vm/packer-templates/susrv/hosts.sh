#!/bin/bash

sed -ri "/127.0.1.1/s/^.*$/10.0.0.23\tsusrv.rtfm.rbt\tsusrv/" /etc/hosts 
