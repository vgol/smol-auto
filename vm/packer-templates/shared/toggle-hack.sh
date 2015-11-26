#!/bin/bash
# Switch keyboard layout toggle to Control+Shift.

sed -ri -e '/XKBOPTIONS/s/alt_shift/ctrl_shift/' /etc/default/keyboard

