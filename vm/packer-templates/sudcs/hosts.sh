#!/bin/bash

sed -ri "/127.0.1.1/s/^.*$/10.0.0.24\tsudcs.rtfm.rbt\tsudcs/" /etc/hosts 
