#!/bin/bash

sed -ri "/127.0.1.1/s/^.*$/10.0.10.7\tsuac.gtfo.rbt\tsuac/" /etc/hosts 
