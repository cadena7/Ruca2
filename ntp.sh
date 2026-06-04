#!/bin/bash


sleep 10
sudo systemctl stop ntp && sudo ntpdate -b 192.168.0.253 && sudo systemctl restart ntp && sudo ntpq -p