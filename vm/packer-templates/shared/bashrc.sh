#!/bin/bash
# Set colors, ls and grep aliases.

root_brc="/root/.bashrc"
first=$(grep 1000 /etc/passwd | cut -d':' -f1)
user_brc="/home/${first}/.bashrc"

# root
sed -ri -e"\
/^# export LS_OPTIONS=/s/^# //
/^# eval \"\`dircolors\`\"/s/^# //
/^# alias ls=/s/^# //
/^# alias ll=/s/^# //
" $root_brc

cat >> $root_brc <<EOF

# Added by bashrc.sh:
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

EOF
# First user
sed -ri -e "
/^( |\t)*#alias ll=/s/#//
/^( |\t)*#alias grep=/s/#//
/^( |\t)*#alias fgrep=/s/#//
/^( |\t)*#alias egrep=/s/#//
" $user_brc

