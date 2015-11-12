#!/bin/bash

sed -ri "/127.0.1.1/s/^.*$/10.0.10.6\tsudcm.gtfo.rbt\tsudcm/" /etc/hosts
