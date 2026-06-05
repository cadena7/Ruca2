#!/usr/bin/env python3

'''
RUCA 2.0 - STATUS ENDPOINT MQTT
Version 0.1-dev          29/Julio/2024
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

El control esta implementado mediante un código en lenguaje Python 3,
basado en una microcomputadora de la línea Raspberry Pi 3 modelo B.

Este programa es un interprete de MQTT a sockets locales para comunicarse con el instrumento.

Comandos que Ejecuta el Servidor de sockets:

REDUCTOR (1-3): mete el reductor azul (1) o reductor rojo (2) y lo saca (3)
RUEDA (1-8): va hacia el número de filtro indicado
POLARIZA (1-5): va hacia el número de polarizador indicado
ESTADO: devuelve el estado de las variables en formato json
INICIO: busca inicio de los motores de paso

Ejemplos con Mosquitto:

Subscribirse a todos los topicos:
mosquitto_sub -h 192.168.0.243 -t oan/control/1.5m/ruca2/# -d

mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/control -m INICIO
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/control -m ESTADO
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/control -m NOMBRES
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/rueda -m 5
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/reductor -m 2

mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/cambianombres -m (nombres deseados en diccionario json)

Funciones Añadidas:

Ver. 0.1 - Publica estado cada 2 segundos para refrescar la variable RUEDA_SWITCH
'''



# Modulos externos
import time, datetime
import os
import sys
import paho.mqtt.client as mqtt
import subprocess
from threading import Thread
import simplejson as json

# MQTT IP
LOCAL_IP = "nc 192.168.0.34 6666"
RUCA_IP = "nc localhost 6666"
MQTT_HOST = "192.168.0.243"
#MQTT_HOST = "localhost"

MQTT_TOPIC = "oan/control/1.5m/ruca2/#"

MQTT_RUEDA = "oan/control/1.5m/ruca2/rueda"
MQTT_POLARIZA = "oan/control/1.5m/ruca2/polarizador"
MQTT_REDUCTOR = "oan/control/1.5m/ruca2/reductor"
MQTT_CONTROL = "oan/control/1.5m/ruca2/control"

MQTT_ESTADO = "oan/control/1.5m/ruca2/estado"
MQTT_NOMBRES = "oan/control/1.5m/ruca2/nombres"
MQTT_CAMBIA_NOMBRES = "oan/control/1.5m/ruca2/cambianombres"

# MQTT on_connect
def on_connect(client, user_data, flags, rc):
    print ("Resultado de conexion: " + str(rc))
    client.subscribe(MQTT_TOPIC)
    print ("Conectado a: " + MQTT_TOPIC)


def publicaestado():
    estado = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    estado1 = estado.communicate(str.encode("ESTADO"))[0]  #regresa un tuple [0,1]
    print ("[+] SOLICITANDO VARIABLES ESTADO RUCA2")
    #print(estado1)
    estadojson = estado1.decode('utf-8')    #decodificar el mensaje
    #print(estadojson)
    estado.kill()
    estadojson1 = json.loads(estadojson)
    msg = {
        'RUEDA_INICIO': estadojson1['RUEDA_INICIO'],
        'RUEDA_INDICE': estadojson1['RUEDA_INDICE'],
        'POLARIZA_INICIO': estadojson1['POLARIZA_INICIO'],
        'POLARIZA_INDICE': estadojson1['POLARIZA_INDICE'],
        'REDUCTOR_AZUL': estadojson1['REDUCTOR_AZUL'],
        'REDUCTOR_ROJO': estadojson1['REDUCTOR_ROJO'],
        'REDUCTOR_FUERA': estadojson1['REDUCTOR_FUERA'],
        'REDUCTOR_INDICE': estadojson1['REDUCTOR_INDICE'],
        'RUEDA_FRENO': estadojson1['RUEDA_FRENO'],
        'POLARIZA_FRENO': estadojson1['POLARIZA_FRENO'],
        'REDUCTOR_FRENO': estadojson1['REDUCTOR_FRENO'],
        'RUEDA_INDICE_SET': estadojson1['RUEDA_INDICE_SET'],
        'POLARIZA_INDICE_SET': estadojson1['POLARIZA_INDICE_SET'],
        'REDUCTOR_SET': estadojson1['REDUCTOR_SET'],
        'RUEDA_PASOS': estadojson1['RUEDA_PASOS'],
        'POLARIZA_PASOS': estadojson1['POLARIZA_PASOS'],
        'REDUCTOR_PASOS': estadojson1['REDUCTOR_PASOS'],
        'FIRST_INIT_RUEDA': estadojson1['FIRST_INIT_RUEDA'],
        'FIRST_INIT_POLARIZA': estadojson1['FIRST_INIT_POLARIZA'],
        'FIRST_INIT_REDUCTOR': estadojson1['FIRST_INIT_REDUCTOR'],
        'RUEDA_FRENO_SENSOR': estadojson1['RUEDA_FRENO_SENSOR'],
        'POLARIZA_FRENO_SENSOR': estadojson1['POLARIZA_FRENO_SENSOR'],
        'RUEDA_PARO_EMERGENCIA': estadojson1['RUEDA_PARO_EMERGENCIA'],
        'RUEDA_SPEED': estadojson1['RUEDA_SPEED'],
        'RUEDA_SWITCH': estadojson1['RUEDA_SWITCH'],
        'RUEDA_ESTADO': estadojson1['RUEDA_ESTADO']
        }
    msg_json = json.dumps(msg, separators=(',', ':'), sort_keys=True) #data serialized
    #print(msg_json)
    client.publish(MQTT_ESTADO, msg_json, retain=True)
    print ("[+] STATUS DE VARIABLES ENVIADO OK")


def publicanombres():
    nombres = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    nombres1 = nombres.communicate(str.encode("NOMBRE"))[0]  #regresa un tuple [0,1]
    print ("[+] SOLICITANDO NOMBRES FILTROS RUCA2")
    #print(nombres1)
    nombresjson = nombres1.decode('utf-8')    #decodificar el mensaje
    #print(nombresjson)
    nombres.kill()
    nombresjson1 = json.loads(nombresjson)
    msg = {
        'Filtro01': nombresjson1['Filtro01'],
        'Filtro02': nombresjson1['Filtro02'],
        'Filtro03': nombresjson1['Filtro03'],
        'Filtro04': nombresjson1['Filtro04'],
        'Filtro05': nombresjson1['Filtro05'],
        'Filtro06': nombresjson1['Filtro06'],
        'Filtro07': nombresjson1['Filtro07'],
        'Filtro08': nombresjson1['Filtro08'],
        'Polariza01': nombresjson1['Polariza01'],
        'Polariza02': nombresjson1['Polariza02'],
        'Polariza03': nombresjson1['Polariza03'],
        'Polariza04': nombresjson1['Polariza04'],
        'Polariza05': nombresjson1['Polariza05'],
        'Reductor01': nombresjson1['Reductor01'],
        'Reductor02': nombresjson1['Reductor02'],
        'Reductor03': nombresjson1['Reductor03']
        }
    msg_json = json.dumps(msg, separators=(',', ':'), sort_keys=True) #data serialized
    #print(msg_json)
    client.publish(MQTT_NOMBRES, msg_json, retain=True)
    print ("[+] NAMES ENVIADOS OK")


#Loop que publica los datos de estado en el broker MQTT
class MQTTLOOP(Thread):
    def __init__(self):
        Thread.__init__(self)
        print ("[+] Inicia thread de monitoreo de estado y publicacion en MQTT")

    def run(self):
        while True :
            try:
                publicaestado()
            except:
                pass
            time.sleep(2) #actualiza el estado en MQTT cada 2 segundos

# Programa Principal
try:
    print ("[+] INTERPRETE MQTT STATUS DE LA RUCA 2.0 Iniciado! Presione CTRL+C para Salir")
    client = mqtt.Client()
    client.connect(MQTT_HOST, 1883, 60)
    client.on_connect = on_connect

    MQTTloop = MQTTLOOP()
    MQTTloop.setDaemon(True)
    MQTTloop.start()

    while True:
        time.sleep(2) #llama la funcion de publicar estado cada 2 segundos


except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    print("Adios Viajero")
    sys.exit()
