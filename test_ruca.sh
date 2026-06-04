#!/bin/bash

HOST="192.168.0.34"
PORT=6666

DELAY=5        # segundos entre comandos
CYCLES=10      # número de ciclos

echo "Iniciando prueba RUCA..."
echo "Host: $HOST | Puerto: $PORT"
echo "Ciclos: $CYCLES | Delay: $DELAY s"
echo "-----------------------------------"

for ((i=1; i<=CYCLES; i++))
do
    POS=$((RANDOM % 8 + 1))

    echo ""
    echo "[$i/$CYCLES] Enviando: RUEDA $POS"

    RESP=$(echo "RUEDA $POS" | nc $HOST $PORT)
    echo "Respuesta RUEDA: $RESP"

    echo "Solicitando ESTADO..."
    EST=$(echo "ESTADO" | nc $HOST $PORT)
    echo "Respuesta ESTADO:"
    echo "$EST"

    echo "Esperando $DELAY segundos..."
    sleep $DELAY

    echo "-----------------------------------"
done

echo "Prueba terminada."