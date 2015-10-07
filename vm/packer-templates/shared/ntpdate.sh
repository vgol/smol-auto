#!/bin/bash

printf "*/10 * * * *\troot\t/usr/sbin/ntpdate ntp" > /etc/cron.d/ntpdate
