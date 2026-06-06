#!/bin/bash


prog=ruca2.py

echo "Running $prog"

kill $(pgrep -f $prog)

cd /home/observa/cadena/Ruca2_UI

#export GTK_THEME=Nordic-darker

./$prog &