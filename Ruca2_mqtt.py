#!/usr/bin/env python3

'''
RUCA 2.0 - ENDPOINT MQTT
Version 0.8-dev          4/Junio/2026
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

Ver. 0.8 - Se agregaron las variables B_START, B_STOP, B_UP y B_DOWN al estado publicado por MQTT
Ver. 0.7 - Dos nuevas variables de estado: RUEDA_SWITCH y RUEDA_SPEED
Ver. 0.6 - IP Localhost
Ver. 0.5 - Agregue try, except en el thread de monitoreo MQTT de la Ruca
Ver. 0.4 - Fix JSON payload
Ver. 0.3 - Al llegar a cada posicion manda actualizar topico Estado
Ver. 0.2 - Ips de brokers y ruca actualizados
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


# MQTT on_message
def on_message(client, user_data, msg):
    #status = str(msg.payload)
    #print ("Received message '" + str(msg.payload.decode("utf-8")) + "' on topic '" + str(msg.topic) + "' with QoS " + str(msg.qos))
    topic = str(msg.topic)   # decodificar la string
    status = str(msg.payload.decode("utf-8"))   # decodificar la string
    status2 = status.upper() # convertir a mayusculas
    print ("Topico MQTT: " + topic + " Mensaje MQTT: " + status)

    if topic == MQTT_RUEDA:
        if status2 == '1':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 1")
            rueda1 = rueda.communicate(str.encode("RUEDA 1"))
            rueda.kill()
            print ("[+] RUEDA 1 OK")
            publicaestado()

        elif status2 == '2':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 2")
            rueda1 = rueda.communicate(str.encode("RUEDA 2"))
            rueda.kill()
            print ("[+] RUEDA 2 OK")
            publicaestado()

        elif status2 == '3':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 3")
            rueda1 = rueda.communicate(str.encode("RUEDA 3"))
            rueda.kill()
            print ("[+] RUEDA 3 OK")
            publicaestado()

        elif status2 == '4':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 4")
            rueda1 = rueda.communicate(str.encode("RUEDA 4"))
            rueda.kill()
            print ("[+] RUEDA 4 OK")
            publicaestado()

        elif status2 == '5':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 5")
            rueda1 = rueda.communicate(str.encode("RUEDA 5"))
            rueda.kill()
            print ("[+] RUEDA 5 OK")
            publicaestado()

        elif status2 == '6':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 6")
            rueda1 = rueda.communicate(str.encode("RUEDA 6"))
            rueda.kill()
            print ("[+] RUEDA 6 OK")
            publicaestado()

        elif status2 == '7':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 7")
            rueda1 = rueda.communicate(str.encode("RUEDA 7"))
            rueda.kill()
            print ("[+] RUEDA 7 OK")
            publicaestado()

        elif status2 == '8':
            rueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO RUEDA 8")
            rueda1 = rueda.communicate(str.encode("RUEDA 8"))
            rueda.kill()
            print ("[+] RUEDA 8 OK")
            publicaestado()


    elif topic == MQTT_POLARIZA:
        if status2 == '1':
            polariza = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO POLARIZA 1")
            polariza1 = polariza.communicate(str.encode("POLARIZA 1"))
            polariza.kill()
            print ("[+] POLARIZA 1 OK")
            publicaestado()

        elif status2 == '2':
            polariza = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO POLARIZA 2")
            polariza1 = polariza.communicate(str.encode("POLARIZA 2"))
            polariza.kill()
            print ("[+] POLARIZA 2 OK")
            publicaestado()

        elif status2 == '3':
            polariza = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO POLARIZA 3")
            polariza1 = polariza.communicate(str.encode("POLARIZA 3"))
            polariza.kill()
            print ("[+] POLARIZA 3 OK")
            publicaestado()

        elif status2 == '4':
            polariza = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO POLARIZA 4")
            polariza1 = polariza.communicate(str.encode("POLARIZA 4"))
            polariza.kill()
            print ("[+] POLARIZA 4 OK")
            publicaestado()

        elif status2 == '5':
            polariza = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO POLARIZA 5")
            polariza1 = polariza.communicate(str.encode("POLARIZA 5"))
            polariza.kill()
            print ("[+] POLARIZA 5 OK")
            publicaestado()


    elif topic == MQTT_REDUCTOR:
        if status2 == '1':
            reductor = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO REDUCTOR 1")
            reductor1 = reductor.communicate(str.encode("REDUCTOR 1"))
            reductor.kill()
            print ("[+] REDUCTOR 1 OK")
            publicaestado()

        elif status2 == '2':
            reductor = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO REDUCTOR 2")
            reductor1 = reductor.communicate(str.encode("REDUCTOR 2"))
            reductor.kill()
            print ("[+] REDUCTOR 2 OK")
            publicaestado()

        elif status2 == '3':
            reductor = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO REDUCTOR 3")
            reductor1 = reductor.communicate(str.encode("REDUCTOR 3"))
            reductor.kill()
            print ("[+] REDUCTOR 3 OK")
            publicaestado()


    elif topic == MQTT_CONTROL:
        if status2 == 'STATUS' or status2 == "ESTADO":
            publicaestado()

        elif status2 == 'NAMES' or status2 == "NOMBRES":
            publicanombres()

        elif status2 == 'INIT' or status2 == "INICIO":
            startrueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO INICIO RUEDA")
            startrueda1 = startrueda.communicate(str.encode("INICIO"))
            startrueda.kill()
            print ("[+] INICIO RUEDA OK")
            publicaestado()

        elif status2 == 'STOP' or status2 == "PARA":
            stoprueda = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO STOP RUEDA")
            stoprueda1 = stoprueda.communicate(str.encode("STOP"))
            stoprueda.kill()
            print ("[+] STOP RUEDA OK")
            publicaestado()


    elif topic == MQTT_CAMBIA_NOMBRES:
        nombresviejos = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        nombresviejos1 = nombresviejos.communicate(str.encode("NOMBRE"))[0]  #regresa un tuple [0,1]
        print ("[+] SOLICITANDO NOMBRES FILTROS")
        #print(nombresviejos1)
        nombresviejos2 = nombresviejos1.decode('utf-8')    #decodificar nombres viejos
        nombresviejos.kill()
        nombresviejosjson = json.loads(nombresviejos2) #viejos nombres
        print(nombresviejosjson)
        try:
            nombresnuevosjson = json.loads(status) #nuevos nombres
            print(nombresnuevosjson)
            if 'Filtro01' in nombresnuevosjson:
                N_FILTRO_01 = nombresnuevosjson['Filtro01']
            else:
                N_FILTRO_01 = nombresviejosjson['Filtro01']
            if 'Filtro02' in nombresnuevosjson:
                N_FILTRO_02 = nombresnuevosjson['Filtro02']
            else:
                N_FILTRO_02 = nombresviejosjson['Filtro02']
            if 'Filtro03' in nombresnuevosjson:
                N_FILTRO_03 = nombresnuevosjson['Filtro03']
            else:
                N_FILTRO_03 = nombresviejosjson['Filtro03']
            if 'Filtro04' in nombresnuevosjson:
                N_FILTRO_04 = nombresnuevosjson['Filtro04']
            else:
                N_FILTRO_04 = nombresviejosjson['Filtro04']
            if 'Filtro05' in nombresnuevosjson:
                N_FILTRO_05 = nombresnuevosjson['Filtro05']
            else:
                N_FILTRO_05 = nombresviejosjson['Filtro05']
            if 'Filtro06' in nombresnuevosjson:
                N_FILTRO_06 = nombresnuevosjson['Filtro06']
            else:
                N_FILTRO_06 = nombresviejosjson['Filtro06']
            if 'Filtro07' in nombresnuevosjson:
                N_FILTRO_07 = nombresnuevosjson['Filtro07']
            else:
                N_FILTRO_07 = nombresviejosjson['Filtro07']
            if 'Filtro08' in nombresnuevosjson:
                N_FILTRO_08 = nombresnuevosjson['Filtro08']
            else:
                N_FILTRO_08 = nombresviejosjson['Filtro08']

            if 'Polariza01' in nombresnuevosjson:
                N_POLARIZA_01 = nombresnuevosjson['Polariza01']
            else:
                N_POLARIZA_01 = nombresviejosjson['Polariza01']
            if 'Polariza02' in nombresnuevosjson:
                N_POLARIZA_02 = nombresnuevosjson['Polariza02']
            else:
                N_POLARIZA_02 = nombresviejosjson['Polariza02']
            if 'Polariza03' in nombresnuevosjson:
                N_POLARIZA_03 = nombresnuevosjson['Polariza03']
            else:
                N_POLARIZA_03 = nombresviejosjson['Polariza03']
            if 'Polariza04' in nombresnuevosjson:
                N_POLARIZA_04 = nombresnuevosjson['Polariza04']
            else:
                N_POLARIZA_04 = nombresviejosjson['Polariza04']
            if 'Polariza05' in nombresnuevosjson:
                N_POLARIZA_05 = nombresnuevosjson['Polariza05']
            else:
                N_POLARIZA_05 = nombresviejosjson['Polariza05']

            if 'Reductor01' in nombresnuevosjson:
                N_REDUCTOR_01 = nombresnuevosjson['Reductor01']
            else:
                N_REDUCTOR_01 = nombresviejosjson['Reductor01']
            if 'Reductor02' in nombresnuevosjson:
                N_REDUCTOR_02 = nombresnuevosjson['Reductor02']
            else:
                N_REDUCTOR_02 = nombresviejosjson['Reductor02']
            if 'Reductor03' in nombresnuevosjson:
                N_REDUCTOR_03 = nombresnuevosjson['Reductor03']
            else:
                N_REDUCTOR_03 = nombresviejosjson['Reductor03']

            nuevosnombres = {
                    'Filtro01': N_FILTRO_01,
                    'Filtro02': N_FILTRO_02,
                    'Filtro03': N_FILTRO_03,
                    'Filtro04': N_FILTRO_04,
                    'Filtro05': N_FILTRO_05,
                    'Filtro06': N_FILTRO_06,
                    'Filtro07': N_FILTRO_07,
                    'Filtro08': N_FILTRO_08,
                    'Polariza01': N_POLARIZA_01,
                    'Polariza02': N_POLARIZA_02,
                    'Polariza03': N_POLARIZA_03,
                    'Polariza04': N_POLARIZA_04,
                    'Polariza05': N_POLARIZA_05,
                    'Reductor01': N_REDUCTOR_01,
                    'Reductor02': N_REDUCTOR_02,
                    'Reductor03': N_REDUCTOR_03
                    }

            salida_json = json.dumps(nuevosnombres, separators=(',', ':'), sort_keys=True) #data serialized
            cambio = subprocess.Popen(RUCA_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO CAMBIO NOMBRES EN RUCA2")
            cambio1 = cambio.communicate(str.encode("CAMBIO ") + str.encode(salida_json))
            cambio.kill()
            print ("[+] CAMBIA NOMBRES EN RUCA2 OK")
            print(salida_json)
        except:
            print ("[-] ERROR CAMBIANDO NOMBRES EN RUCA2")
            pass
        publicanombres()


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
        'RUEDA_ESTADO': estadojson1['RUEDA_ESTADO'],
        'B_START': estadojson1['B_START'],
        'B_STOP': estadojson1['B_STOP'],
        'B_UP': estadojson1['B_UP'],
        'B_DOWN': estadojson1['B_DOWN']
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
            time.sleep(20) #actualiza el estado en MQTT cada 20 segundos
            try:
                publicanombres()
            except:
                pass
            time.sleep(20) #actualiza el estado en MQTT cada 20 segundos

# Programa Principal
try:
    print ("[+] INTERPRETE MQTT DE LA RUCA 2.0 Iniciado! Presione CTRL+C para Salir")
    client = mqtt.Client()
    client.connect(MQTT_HOST, 1883, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    #client.loop_start()

    MQTTloop = MQTTLOOP()
    MQTTloop.setDaemon(True)
    MQTTloop.start()
    client.loop_forever()


except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    print("Adios Viajero")
    client.loop_stop()
    sys.exit()
