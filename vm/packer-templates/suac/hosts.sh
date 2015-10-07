#!/bin/bash

sed -ri "/127.0.1.1/s/^.*$/10.0.0.25\tsuac.rtfm.rbt\tsuac/" /etc/hosts 
