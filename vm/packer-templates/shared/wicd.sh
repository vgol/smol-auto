#!/bin/bash

#rm -f /etc/xdg/autostart/fly-admin-wicd.desktop
echo "Hidden=true" >> /etc/xdg/autostart/fly-admin-wicd.desktop
update-rc.d wicd disable
