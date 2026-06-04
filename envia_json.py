#!/usr/bin/env python3

'''
RUCA 2.0 - RUEDA DE FILTROS ENDPOINT MQTT TESTER
Version 0.1-dev          19/Oct/2022
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx


Funciones Añadidas:

Ver. 0.1 - En Desarrollo
'''



# Modulos externos
import time, datetime
import os
import sys
import paho.mqtt.client as mqtt
import subprocess
from threading import Thread
import simplejson as json

# TELNET IP
RUCA_IP = "nc 192.168.0.34 6666"


# MQTT IP
MQTT_HOST = "192.168.0.243"

MQTT_JSON = "oan/control/1.5m/ruca2/cambianombres"



def nombresjsonmqtt():
    try:
        salida = {
            'Filtro01': 'A',
            'Filtro02': 'B',
            'Filtro03': 'C',
            'Filtro04': 'D',
            'Filtro05': 'E',
            'Filtro06': 'F',
            'Filtro07': 'G',
            'Filtro08': 'H',
            'Polariza01': 'I',
            'Polariza02': 'J',
            'Polariza03': 'K',
            'Polariza04':'L',
            'Polariza05': 'M',
            'Reductor01': 'N',
            'Reductor02': 'O',
            'Reductor03': 'P'
            }
        salida_json = json.dumps(salida, separators=(',', ':'), sort_keys=True) #data serialized
        print(salida_json)
        client.publish(MQTT_JSON, salida_json, retain=False)
        print ("[+] MENSAJE ENVIADO OK")

    except:
        print ("[-] PASO EL ERROR")
        pass

def nombresjsonsocket():
    salida = {
        'Filtro01': '11',
        'Filtro02': '22',
        'Filtro03': '33',
        'Filtro04': '44',
        'Filtro05': '55',
        'Filtro06': '66',
        'Filtro07': '77',
        'Filtro08': '88',
        'Polariza01': '11',
        'Polariza02': '22',
        'Polariza03': '33',
        'Polariza04':'44',
        'Polariza05': '55',
        'Reductor01': '11',
        'Reductor02': '22',
        'Reductor03': '33'
        }
    salida_json = json.dumps(salida, separators=(',', ':'), sort_keys=True) #data serialized
    print(salida_json)

    cambio = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO CAMBIO")
    cambio1 = cambio.communicate(str.encode("CAMBIO ") + str.encode(salida_json))
    cambio.kill()
    print(salida_json)
    print ("[+] MENSAJE ENVIADO OK")


# Programa Principal
try:
    print ("[+] ENVIANDO UN MENSAJE MQTT EN JSON AL RUCA 2.0 - RUEDA DE FILTROS ENDPOINT")
    client = mqtt.Client()
    client.connect(MQTT_HOST, 1883, 60)
    #nombresjsonsocket()
    nombresjsonmqtt()


except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    print("Adios Viajero")
    sys.exit()
