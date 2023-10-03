#!/usr/bin/env python3

'''
RUCA 2.0 - PRUEBAS
Version 0.2-dev         21/Jun/2018
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

Rueda de filtros RUCA 2.0, consiste en una rueda de filtros, un polarizador,
dos reductores focales y una platina giratoria.
El sistema consta de:
1 - Motor a Pasos para Rueda de filtros
1 - Motor a Pasos para Rueda de polarizadores
1 - Motor a Pasos para Reductores focales
1 - Motor DC con lectura de encoder para Platina giratoria
2 - Interruptores límite N.A. para filtros (Indice y Posiciones 0-7)
2 - Interruptores límite N.A. para polarizadores (Indice y Posiciones 0-7)
2 - Interruptores límite N.A. para reductores (Indices: Dentro y Afuera)
2 - Interruptores límite N.A. para platina (Indice, límite, límite duro (sin lectura))

El control esta implementado mediante un código en lenguaje Python 3,
basado en una microcomputadora de la línea Raspberry Pi 3 modelo B.

Comandos que Ejecuta el Servidor:

OPEN: abre tapa a la posicion de apertura
CLOSE: cierra tapa a la posicion de cierre
MUEVE #MOTOR (+/-)#PASOS: mueve el numero de pasos indicado
IR #MOTOR (+/-)#POSICION: va a la posición indicada
POS #MOTOR: devuelve la posición del motor
INICIO: reinicia un motor de pasos

Funciones Añadidas:




Ver. 0.2 - En Desarrollo
Ver. 0.1 - Implementada
'''

# Modulos externos
#from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor
from Adafruit_MotorHAT.Adafruit_MotorHAT_Motors import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor
import RPi.GPIO as GPIO
import time
import atexit
import os
import sys
from threading import Thread
import random
import socket
import subprocess
import simplejson as json
import queue as Queue
import simplejson as json


# Entradas
RUEDA_INICIO = 0
RUEDA_INDICE = 0
POLARIZA_INICIO = 0
POLARIZA_INDICE = 0
REDUCTOR_DENTRO = 0
REDUCTOR_FUERA = 0

# Salidas
RUEDA_FRENO = 0
POLARIZA_FRENO = 0
REDUCTOR_FRENO = 0

# GPIOS Entradas
RUEDA_INICIO_PIN = 4
RUEDA_INDICE_PIN = 17
POLARIZA_INICIO_PIN = 27
POLARIZA_INDICE_PIN = 22
REDUCTOR_DENTRO_PIN = 5
REDUCTOR_FUERA_PIN = 6

# GPIOS Salidas
RUEDA_FRENO_PIN = 23
POLARIZA_FRENO_PIN = 12
REDUCTOR_FRENO_PIN = 16

# Posición deseadas
RUEDA_INDICE_SET = 0        #1-8
POLARIZA_INDICE_SET = 0     #1-8
REDUCTOR_SET = 0            #1 DENTRO , 2 FUERA

# Pasos de Motores
RUEDA_PASOS = 0
POLARIZA_PASOS = 0
REDUCTOR_PASOS = 0


# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
                                            # GPIO pulled down, detecta  3.3V con la interrupcion
GPIO.setup(RUEDA_INICIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)       #4   Pull_down
GPIO.setup(RUEDA_INDICE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)       #17  Pull_down
GPIO.setup(POLARIZA_INICIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    #27  Pull_down
GPIO.setup(POLARIZA_INDICE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    #22  Pull_down
GPIO.setup(REDUCTOR_DENTRO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    #5  N.O.  Pull_down
GPIO.setup(REDUCTOR_FUERA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #6  N.C.  Pull_down     detecta cambio a GND con la interrupción

GPIO.setup(RUEDA_FRENO_PIN, GPIO.OUT)       #23
GPIO.setup(POLARIZA_FRENO_PIN, GPIO.OUT)    #12
GPIO.setup(REDUCTOR_FRENO_PIN, GPIO.OUT)    #16



# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 6666
BUFFER_SIZE = 2048  # Usually 1024, but we need quick response

# create an INET, STREAMing socket
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#tcpServer.setblocking(0)    #Non blocking
# bind the socket to a public host, and a well-known port
tcpServer.bind((TCP_IP, TCP_PORT))
threads = []
#message_queues = {}


# ADAFRUIT MOTORHATS
# bottom hat is default address 0x60
bottomhat = Adafruit_MotorHAT(addr=0x60)
# top hat has A0 jumper closed, so its address 0x61
#tophat = Adafruit_MotorHAT(addr=0x61)

# create empty threads (these will hold the stepper's threads)
st1 = Thread()


RUEDA_MOTOR = bottomhat.getStepper(200, 1)      # 200 steps/rev, motor port #1
#POLARIZA_MOTOR = bottomhat.getStepper(200, 2)      # 200 steps/rev, motor port #2
#REDUCTOR_MOTOR = tophat.getStepper(200, 1)      # 200 steps/rev, motor port #1

RUEDA_MOTOR.setSpeed(60)          # 60 RPM
#POLARIZA_MOTOR.setSpeed(60)          # 60 RPM
#REDUCTOR_MOTOR.setSpeed(60)          # 60 RPM

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    #tophat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    #tophat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    #tophat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    #tophat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)



def stepper_worker(stepper, numsteps, direction, style):
    #print("Steppin!")
    stepper.step(numsteps, direction, style)
    #print("Done")

# Funciones Callback
# these will run in another thread when our events are detected
def rueda_inicio(channel):
    global RUEDA_INICIO, RUEDA_INDICE, RUEDA_PASOS
    time.sleep(0.005) # debounce for 5mSec
    if GPIO.input(RUEDA_INICIO_PIN):
        RUEDA_INICIO = 1
        print ("<<rising edge detected on 4>>")
        print ("RUEDA_INICIO = " + str(RUEDA_INICIO))
        RUEDA_INDICE = 1
        print ("RUEDA_INDICE = " + str(RUEDA_INDICE))
        RUEDA_PASOS = 0
        print ("RUEDA_PASOS = " + str(RUEDA_PASOS))
    else:
        RUEDA_INICIO = 0
        print ("<<falling edge detected on 4>>")
        print ("RUEDA_INICIO = " + str(RUEDA_INICIO))



def rueda_indice(channel):
    global RUEDA_INDICE, RUEDA_INICIO
    time.sleep(0.005) # debounce for 5mSec
    if GPIO.input(RUEDA_INDICE_PIN):
        if GPIO.input(RUEDA_INICIO_PIN):
            RUEDA_INDICE = 1
        else:
            RUEDA_INDICE = RUEDA_INDICE + 1
    print ("<<rising edge detected on 17>>")
    print ("RUEDA_INDICE = " + str(RUEDA_INDICE))


def polariza_inicio(channel):
    global POLARIZA_INICIO, POLARIZA_INDICE
    time.sleep(0.005) # debounce for 5mSec
    if GPIO.input(POLARIZA_INICIO_PIN):
        POLARIZA_INICIO = 1
        print ("rising edge detected on 27")
        POLARIZA_INDICE = 1
    else:
        POLARIZA_INICIO = 0
        print ("falling edge detected on 27")


def polariza_indice(channel):
    global POLARIZA_INDICE
    time.sleep(0.005) # debounce for 5mSec
    POLARIZA_INDICE = POLARIZA_INDICE + 1
    print ("rising edge detected on 22")


def reductor_dentro(channel):
    global REDUCTOR_DENTRO
    time.sleep(0.005) # debounce for 5mSec
    if GPIO.input(REDUCTOR_DENTRO_PIN):
        REDUCTOR_DENTRO = 1
        print ("rising edge detected on 5")
    else:
        REDUCTOR_DENTRO = 0
        print ("falling edge detected on 5")


def reductor_fuera(channel):
    global REDUCTOR_FUERA
    time.sleep(0.005) # debounce for 5mSec
    if GPIO.input(REDUCTOR_FUERA_PIN):
        REDUCTOR_FUERA = 0
        print ("rising edge detected on 6")
    else:
        REDUCTOR_FUERA = 1
        print ("falling edge detected on 6")




# Funciones
# Detectamos interrupciones
def initInterrupciones():
    # when a rising edge is detected on gpio, regardless of whatever
    # else is happening in the program, the function my_callback will be run
    GPIO.add_event_detect(RUEDA_INICIO_PIN, GPIO.BOTH, callback=rueda_inicio, bouncetime=200)
    GPIO.add_event_detect(RUEDA_INDICE_PIN, GPIO.RISING, callback=rueda_indice, bouncetime=200)
    GPIO.add_event_detect(POLARIZA_INICIO_PIN, GPIO.BOTH, callback=polariza_inicio, bouncetime=200)
    GPIO.add_event_detect(POLARIZA_INDICE_PIN, GPIO.RISING, callback=polariza_indice, bouncetime=200)
    GPIO.add_event_detect(REDUCTOR_DENTRO_PIN, GPIO.BOTH, callback=reductor_dentro, bouncetime=200)
    GPIO.add_event_detect(REDUCTOR_FUERA_PIN, GPIO.BOTH, callback=reductor_fuera, bouncetime=200)


# Estado inicial de los interruptores
def initStatus():
    RUEDA_INICIO = GPIO.input(RUEDA_INICIO_PIN)
    RUEDA_INDICE = GPIO.input(RUEDA_INDICE_PIN)
    POLARIZA_INICIO = GPIO.input(POLARIZA_INICIO_PIN)
    POLARIZA_INDICE = GPIO.input(POLARIZA_INDICE_PIN)
    REDUCTOR_DENTRO = GPIO.input(REDUCTOR_DENTRO_PIN)
    REDUCTOR_FUERA = GPIO.input(REDUCTOR_DENTRO_PIN)


# Envia a posiciones de inicio las ruedas
def initPos():
    reduc1 = subprocess.Popen(['echo',REDUCTOR,'1','|',"nc","localhost", "6666"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    rueda1 = subprocess.Popen(['echo',RUEDA,'1','|',"nc","localhost", "6666"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    pola1 = subprocess.Popen(['echo',POLA,'1','|',"nc","localhost", "6666"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    reduc0 = subprocess.Popen(['echo',REDUCTOR,'2','|',"nc","localhost", "6666"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)



# Clases
# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread):
    def __init__(self,ip,port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        print ("[+] Nuevo server socket thread iniciado desde " + ip + ":" + str(port))
        conn.send(str.encode('Bienvenido '+ ip + ' procesando comando...' + '\n'))  # echo


    def run(self):
        global RUEDA_INICIO, RUEDA_INDICE, POLARIZA_INICIO, POLARIZA_INDICE, REDUCTOR_DENTRO, REDUCTOR_FUERA, RUEDA_FRENO, POLARIZA_FRENO, REDUCTOR_FRENO, RUEDA_INDICE_SET, POLARIZA_INDICE_SET, REDUCTOR_SET, RUEDA_PASOS, POLARIZA_PASOS, REDUCTOR_PASOS
        #RUEDA_MOTOR    bottomhat 1
        #POLARIZA_MOTOR bottomhat 2
        #REDUCTOR_MOTOR tophat 1

        while True :
            data = conn.recv(2048).strip()
            #message_queues[conn].put(data)
            data = data.decode('utf-8') # decodificar el mensaje
            data = data.upper() # convertir a mayusculas

            print("Comando Recibido: " + data)

            datasplit = data.split(' ')
            comando = datasplit[0]
            print (datasplit) ##debug


            # Comandos
            if comando == 'REDUCTOR':           #EJEMPLO: echo REDUCTOR 1 | nc ip 6666  (del 1 al 2)
                REDUCTOR_SET = int(datasplit[1])
                 #1 DENTRO , 2 FUERA
                if REDUCTOR_SET == 1:
                    while REDUCTOR_DENTRO != 1:
                        #REDUCTOR_MOTOR.step(20, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
                        REDUCTOR_PASOS = REDUCTOR_PASOS + 20
                        conn.send(str.encode('+' + '\n'))  # echo

                elif REDUCTOR_SET == 2:
                    while REDUCTOR_FUERA != 0:
                        #REDUCTOR_MOTOR.step(20, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                        REDUCTOR_PASOS = REDUCTOR_PASOS - 20
                        conn.send(str.encode('-' + '\n'))  # echo

                else:
                    turnOffMotors()

                turnOffMotors()
                conn.send(str.encode('OK: ' + data + '\n'))  # echo
                conn.close()
                break



            elif comando == 'RUEDA':        #EJEMPLO: echo RUEDA 1 | nc ip 6666 (del 1 al 8)
                RUEDA_INDICE_SET = int(datasplit[1])

                while RUEDA_INDICE != RUEDA_INDICE_SET:
                    RUEDA_MOTOR.step(20, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                    RUEDA_PASOS = RUEDA_PASOS + 20
                    conn.send(str.encode('+' + '\n'))  # echo

                    #st1 = Thread(target=stepper_worker, args=(RUEDA_MOTOR, 200, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE))
                    #st1.start()
                    #RUEDA_INDICE = RUEDA_INDICE + 1
                turnOffMotors()
                conn.send(str.encode('OK: ' + data + '\n'))  # echo
                conn.close()
                break



            elif comando == 'POLA':           #EJEMPLO: echo POLA 1 | nc ip 6666  (del 1 al 8)
                POLARIZA_INDICE_SET = int(datasplit[1])

                while POLARIZA_INDICE != POLARIZA_INDICE_SET:
                    #POLARIZA_MOTOR.step(200, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                    POLARIZA_PASOS = POLARIZA_PASOS + 200

                turnOffMotors()
                conn.send(str.encode('OK: ' + data + '\n'))  # echo
                conn.close()
                break


            elif comando == 'INDICE':
                indice = int(datasplit[1])

                RUEDA_INDICE = indice

                conn.send(str.encode('OK: ' + data + '\n'))  # echo
                conn.close()
                break



            elif comando == 'INICIO':       #VA A INICIO DE POSICION
                initPos()
                conn.send(str.encode('OK: ' + data + '\n'))  # echo
                conn.close()
                break



            elif comando == 'ESTADO':     #REGRESA Estado ACTUAL
                print("Peticicion del Cliente por Estado: ", data)
                estado = {
                    'RUEDA_INICIO': RUEDA_INICIO,
                    'RUEDA_INDICE': RUEDA_INDICE,
                    'POLARIZA_INICIO': POLARIZA_INICIO,
                    'POLARIZA_INDICE': POLARIZA_INDICE,
                    'REDUCTOR_DENTRO': REDUCTOR_DENTRO,
                    'REDUCTOR_FUERA': REDUCTOR_FUERA,
                    'RUEDA_FRENO': RUEDA_FRENO,
                    'POLARIZA_FRENO': POLARIZA_FRENO,
                    'REDUCTOR_FRENO': REDUCTOR_FRENO,
                    'RUEDA_INDICE_SET': RUEDA_INDICE_SET,
                    'POLARIZA_INDICE_SET': POLARIZA_INDICE_SET,
                    'REDUCTOR_SET': REDUCTOR_SET,
                    'RUEDA_PASOS': RUEDA_PASOS,
                    'POLARIZA_PASOS': POLARIZA_PASOS,
                    'REDUCTOR_PASOS': REDUCTOR_PASOS
                    }
                estado_json = json.dumps(estado, separators=(',', ':'), sort_keys=True) #data serialized

                conn.send(str.encode(estado_json + '\n'))
                conn.close()
                break



            elif comando == 'EXIT':
                now = time.strftime('%Y-%m-%d %H:%M')
                print(now + ' - Conexion Terminada por el Cliente')
                conn.send(str.encode('Recibido: Adios' + '\n'))
                conn.close()
                break



            else:
                now = time.strftime('%Y-%m-%d %H:%M')
                print(now + ' - No Existe el Comando - Conexion Terminada')
                conn.send(str.encode('Adios' + '\n'))  # echo
                conn.close()
                break


class RuedaThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        print ("[+] Inicia thread de aumento de variable")

    def run(self):
        global RUEDA_INDICE

        while True :

            RUEDA_INDICE = RUEDA_INDICE + 1

            time.sleep(10)


# Programa Principal
try:
    turnOffMotors()
    initInterrupciones()
    initStatus()
    #initPos()
    print("SERVIDOR DE LA RUCA 2.0 Iniciado! Presione CTRL+C para Salir")

    #newoffset = RuedaThread()
    #newoffset.setDaemon(True)
    #newoffset.start()

    while True:
        # become a server socket
        tcpServer.listen(4)
        print ("Esperando por Conexiones...")
        (conn, (ip,port)) = tcpServer.accept()

        newthread = ClientThread(ip,port)
        newthread.start()
        threads.append(newthread)
        #message_queues[newthread] = Queue.Queue()

        # wait until worker threads are done to exit
        for t in threads:
            t.join()



except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    print("Adios Viajero")
    GPIO.cleanup()
    turnOffMotors()
    sys.exit()
    tcpServer.shutdown()
    tcpServer.close()
