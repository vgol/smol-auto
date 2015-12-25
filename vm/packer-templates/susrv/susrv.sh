#!/bin/bash

list="
ald-client-common
ald-admin-common
fly-admin-ald-se
apache2
exim4-daemon-heavy
dovecot-imapd
dovecot-gssapi
postgresql-astra
"

apt-get -y install ${list}
apt-get clean
