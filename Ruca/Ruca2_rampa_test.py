#!/usr/bin/env python3

'''
RUCA 2.0 - RUEDA DE FILTROS
Version 1.6-dev          04/Abril/2024
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

'''

# Modulos externos
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

import Ruca2_variables



# GPIOS Entradas
RUEDA_INICIO_PIN = 4
RUEDA_INDICE_PIN = 17
POLARIZA_INICIO_PIN = 27
POLARIZA_INDICE_PIN = 22
REDUCTOR_AZUL_PIN = 5
REDUCTOR_ROJO_PIN = 6
RUEDA_FRENO_IN_PIN = 18
POLARIZA_FRENO_IN_PIN = 24

# GPIOS Salidas
RUEDA_FRENO_OUT_PIN = 23
POLARIZA_FRENO_OUT_PIN = 12
REDUCTOR_FRENO_OUT_PIN = 16


# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme                   # GPIO pulled down, detecta  3.3V con la interrupcion
GPIO.setwarnings(False)
GPIO.setup(RUEDA_INICIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)        #4   Pull_down
GPIO.setup(RUEDA_INDICE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)        #17  Pull_down
GPIO.setup(POLARIZA_INICIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #27  Pull_down
GPIO.setup(POLARIZA_INDICE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #22  Pull_down
GPIO.setup(REDUCTOR_AZUL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)       #5  N.O.  Pull_down
GPIO.setup(REDUCTOR_ROJO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)       #6  N.O.  Pull_down
#GPIO.setup(REDUCTOR_FUERA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #24  N.O.  Pull_down
GPIO.setup(RUEDA_FRENO_IN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)      #18  N.O.  Pull_down
GPIO.setup(POLARIZA_FRENO_IN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   #24  N.O.  Pull_down

GPIO.setup(RUEDA_FRENO_OUT_PIN, GPIO.OUT)                                #23
GPIO.setup(POLARIZA_FRENO_OUT_PIN, GPIO.OUT)                             #12
GPIO.setup(REDUCTOR_FRENO_OUT_PIN, GPIO.OUT)                             #16

#RUEDA_FRENO_OUT_PWM = GPIO.PWM(RUEDA_FRENO_OUT_PIN, 1000)  # channel=23 frequency=1Hz
#POLARIZA_FRENO_OUT_PWM = GPIO.PWM(POLARIZA_FRENO_OUT_PIN, 1000)  # channel=12 frequency=1Hz

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 6666
BUFFER_SIZE = 2048  # Usually 1024, but we need quick response

# create an INET, STREAMing socket
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind the socket to a public host, and a well-known port
tcpServer.bind((TCP_IP, TCP_PORT))
threads = []
#message_queues = {}


# ADAFRUIT MOTORHATS
# bottom hat is default address 0x60
bottomhat = Adafruit_MotorHAT(addr=0x60)
# top hat has A0 jumper closed, so its address 0x61
# tophat = Adafruit_MotorHAT(addr=0x61)

RUEDA_MOTOR = bottomhat.getStepper(200, 1)      # 200 steps/rev, motor port #1
# POLARIZA_MOTOR = tophat.getStepper(200, 2)      # 200 steps/rev, motor port #2
# REDUCTOR_MOTOR = tophat.getStepper(200, 1)      # 200 steps/rev, motor port #1

RUEDA_MOTOR.setSpeed(80)          # 60 RPM
# POLARIZA_MOTOR.setSpeed(80)          # 60 RPM
# REDUCTOR_MOTOR.setSpeed(200)          # 200 RPM

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    # tophat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    # tophat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    # tophat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    # tophat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def turnOffRueda():
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)

    '''
def turnOffPolariza():
    tophat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def turnOffReductor():
    tophat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
 '''
# recommended for auto-disabling motors on shutdown!
atexit.register(turnOffMotors)



# Envia a posiciones de inicio al ARRANCAR la rueda de filtros y rueda de polarizadores
def FirstinitPos():
    reduccompletado = 1
    ruedacompletado = 1
    polarizacompletado = 1
    ruedapasosextra = 0
    polarizapasosextra = 0

    variables.FIRST_INIT_RUEDA = 1
    time.sleep(1.0)


# Envia a posiciones de inicio las ruedas de filtros
def initPos():
    print ("[+] Iniciando Rueda de Filtros...")
    variables.FIRST_INIT_RUEDA = 0    # desconoce la inicializada anterior
    #variables.FIRST_INIT_POLARIZA = 0
    variables.FIRST_INIT_REDUCTOR = 0
    variables.RUEDA_INDICE_SET = 0
    #variables.POLARIZA_INDICE_SET = 0
    variables.REDUCTOR_SET = 0
    variables.RUEDA_STOP = 0
    time.sleep(0.3)
    principal = Principal()
    principal.initStatus()
    time.sleep(0.3)
    FirstinitPos()
    print ("[+] Inicializada Rueda de Filtros OK")


#Clase Principal
class Principal():
    def __init__(self):
        GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
        #RUEDA_FRENO_OUT_PWM.start(0)
        GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
        #POLARIZA_FRENO_OUT_PWM.start(0)
        GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
        print ("[+] Variables de la Rueda de Filtros Cargadas")


    # Funciones Callback
    # these will run in another thread when our events are detected
    def rueda_inicio(self, channel):  #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(RUEDA_INICIO_PIN):
            variables.RUEDA_INICIO = 1
            print (">>rising edge detected on RUEDA_INICIO_PIN>>")
            print ("RUEDA_INICIO = " + str(variables.RUEDA_INICIO))
            variables.RUEDA_INDICE = 1
            print ("RUEDA_INDICE = " + str(variables.RUEDA_INDICE))
            variables.RUEDA_PASOS = 0
            print ("RUEDA_PASOS = " + str(variables.RUEDA_PASOS))
            variables.FIRST_INIT_RUEDA = 1
        else:
            variables.RUEDA_INICIO = 0
            print ("<<falling edge detected on RUEDA_INICIO_PIN<<")
            print ("RUEDA_INICIO = " + str(variables.RUEDA_INICIO))
            print ("RUEDA_INDICE = " + str(variables.RUEDA_INDICE))


    def rueda_indice(self, channel):   #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(RUEDA_INDICE_PIN):
            if GPIO.input(RUEDA_INICIO_PIN):
                variables.RUEDA_INDICE = 1
            else:
                if variables.RUEDA_SENTIDO == 1:
                    variables.RUEDA_INDICE = variables.RUEDA_INDICE + 1
                    if variables.RUEDA_INDICE == 9:
                        variables.RUEDA_INDICE = 1
                else:
                    variables.RUEDA_INDICE = variables.RUEDA_INDICE - 1
                    if variables.RUEDA_INDICE == 0:
                        variables.RUEDA_INDICE = 8
        print (">>rising edge detected on RUEDA_INDICE_PIN>>")
        print ("RUEDA_INDICE = " + str(variables.RUEDA_INDICE))


    def polariza_inicio(self, channel):   #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(POLARIZA_INICIO_PIN):
            variables.POLARIZA_INICIO = 1
            print (">>rising edge detected on POLARIZA_INICIO_PIN>>")
            print ("POLARIZA_INICIO = " + str(variables.POLARIZA_INICIO))
            variables.POLARIZA_INDICE = 1
            print ("POLARIZA_INDICE = " + str(variables.POLARIZA_INDICE))
            variables.POLARIZA_PASOS = 0
            print ("POLARIZA_PASOS = " + str(variables.POLARIZA_PASOS))
            variables.FIRST_INIT_POLARIZA = 1
        else:
            variables.POLARIZA_INICIO = 0
            print ("<<falling edge detected on POLARIZA_INICIO_PIN<<")
            print ("POLARIZA_INICIO = " + str(variables.POLARIZA_INICIO))
            print ("POLARIZA_INDICE = " + str(variables.POLARIZA_INDICE))


    def polariza_indice(self, channel):   #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(POLARIZA_INDICE_PIN):
            if GPIO.input(POLARIZA_INICIO_PIN):
                variables.POLARIZA_INDICE = 1
            else:
                if variables.POLARIZA_SENTIDO == 1:
                    variables.POLARIZA_INDICE = variables.POLARIZA_INDICE + 1
                    if variables.POLARIZA_INDICE == 6:
                        variables.POLARIZA_INDICE = 1
                else:
                    variables.POLARIZA_INDICE = variables.POLARIZA_INDICE - 1
                    if variables.POLARIZA_INDICE == 0:
                        variables.POLARIZA_INDICE = 5
        print (">>rising edge detected on POLARIZA_INDICE_PIN>>")
        print ("POLARIZA_INDICE = " + str(variables.POLARIZA_INDICE))


    def reductor_azul(self, channel):   #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(REDUCTOR_AZUL_PIN):
            variables.REDUCTOR_AZUL = 1
            variables.REDUCTOR_FUERA = 0
            variables.REDUCTOR_PASOS = 0
            variables.REDUCTOR_INDICE = 1
            turnOffReductor()
            print (">>rising edge detected on REDUCTOR_AZUL_PIN>>")
            print ("REDUCTOR_AZUL = " + str(variables.REDUCTOR_AZUL))
        else:
            variables.REDUCTOR_AZUL = 0
            variables.REDUCTOR_FUERA = 0
            print ("<<falling edge detected on REDUCTOR_AZUL_PIN<<")
            print ("REDUCTOR_AZUL = " + str(variables.REDUCTOR_AZUL))


    def reductor_rojo(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(REDUCTOR_ROJO_PIN):
            variables.REDUCTOR_ROJO = 1
            variables.REDUCTOR_FUERA = 0
            variables.REDUCTOR_PASOS = 0
            variables.REDUCTOR_INDICE = 2
            variables.FIRST_INIT_REDUCTOR = 1
            turnOffReductor()
            print (">>rising edge detected on REDUCTOR_ROJO_PIN>>")
            print ("REDUCTOR_ROJO = " + str(variables.REDUCTOR_ROJO))
        else:
            variables.REDUCTOR_ROJO = 0
            variables.REDUCTOR_FUERA = 0
            print ("<<falling edge detected on REDUCTOR_ROJO_PIN<<")
            print ("REDUCTOR_ROJO = " + str(variables.REDUCTOR_ROJO))


    def rueda_sensor(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(RUEDA_FRENO_IN_PIN):
            variables.RUEDA_FRENO_SENSOR = 0
            print (">>rising edge detected on RUEDA_FRENO_IN_PIN>>")
            print ("RUEDA_FRENO_SENSOR = " + str(variables.RUEDA_FRENO_SENSOR))
        else:
            variables.RUEDA_FRENO_SENSOR = 1
            print ("<<falling edge detected on RUEDA_FRENO_IN_PIN<<")
            print ("RUEDA_FRENO_SENSOR = " + str(variables.RUEDA_FRENO_SENSOR))


    def polariza_sensor(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(POLARIZA_FRENO_IN_PIN):
            variables.POLARIZA_FRENO_SENSOR = 0
            print (">>rising edge detected on POLARIZA_FRENO_IN_PIN>>")
            print ("POLARIZA_FRENO_SENSOR = " + str(variables.POLARIZA_FRENO_SENSOR))
        else:
            variables.POLARIZA_FRENO_SENSOR = 1
            print ("<<falling edge detected on POLARIZA_FRENO_IN_PIN<<")
            print ("POLARIZA_FRENO_SENSOR = " + str(variables.POLARIZA_FRENO_SENSOR))

    '''
    def reductor_fuera(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(REDUCTOR_FUERA_PIN):
            variables.REDUCTOR_FUERA = 1
            variables.FIRST_INIT_REDUCTOR = 1
            print (">>rising edge detected on REDUCTOR_FUERA_PIN>>")
            print ("REDUCTOR_FUERA = " + str(variables.REDUCTOR_FUERA))
        else:
            variables.REDUCTOR_FUERA = 0
            print ("<<falling edge detected on REDUCTOR_FUERA_PIN<<")
            print ("REDUCTOR_FUERA = " + str(variables.REDUCTOR_FUERA))
    '''


    # Detectamos interrupciones
    def initInterrupciones(self):
        # when a rising edge is detected on gpio, regardless of whatever
        # else is happening in the program, the function my_callback will be run
        GPIO.add_event_detect(RUEDA_INICIO_PIN, GPIO.BOTH, callback=self.rueda_inicio, bouncetime=200)
        GPIO.add_event_detect(RUEDA_INDICE_PIN, GPIO.RISING, callback=self.rueda_indice, bouncetime=200)
        GPIO.add_event_detect(POLARIZA_INICIO_PIN, GPIO.BOTH, callback=self.polariza_inicio, bouncetime=200)
        GPIO.add_event_detect(POLARIZA_INDICE_PIN, GPIO.RISING, callback=self.polariza_indice, bouncetime=200)
        GPIO.add_event_detect(REDUCTOR_AZUL_PIN, GPIO.BOTH, callback=self.reductor_azul, bouncetime=200)
        GPIO.add_event_detect(REDUCTOR_ROJO_PIN, GPIO.BOTH, callback=self.reductor_rojo, bouncetime=200)
        #GPIO.add_event_detect(REDUCTOR_FUERA_PIN, GPIO.BOTH, callback=self.reductor_fuera, bouncetime=200)
        GPIO.add_event_detect(RUEDA_FRENO_IN_PIN, GPIO.BOTH, callback=self.rueda_sensor, bouncetime=200)
        GPIO.add_event_detect(POLARIZA_FRENO_IN_PIN, GPIO.BOTH, callback=self.polariza_sensor, bouncetime=200)


    # Estado inicial de los interruptores
    def initStatus(self):
        variables.RUEDA_INICIO = GPIO.input(RUEDA_INICIO_PIN)
        #variables.RUEDA_INDICE = GPIO.input(RUEDA_INDICE_PIN)
        variables.POLARIZA_INICIO = GPIO.input(POLARIZA_INICIO_PIN)
        #variables.POLARIZA_INDICE = GPIO.input(POLARIZA_INDICE_PIN)
        variables.REDUCTOR_AZUL = GPIO.input(REDUCTOR_AZUL_PIN)
        variables.REDUCTOR_ROJO = GPIO.input(REDUCTOR_ROJO_PIN)
        #variables.REDUCTOR_FUERA = GPIO.input(REDUCTOR_FUERA_PIN)
        variables.RUEDA_FRENO = GPIO.input(RUEDA_FRENO_OUT_PIN)
        variables.POLARIZA_FRENO = GPIO.input(POLARIZA_FRENO_OUT_PIN)
        variables.REDUCTOR_FRENO = GPIO.input(REDUCTOR_FRENO_OUT_PIN)
        variables.RUEDA_FRENO_SENSOR = GPIO.input(RUEDA_FRENO_IN_PIN)
        variables.POLARIZA_FRENO_SENSOR = GPIO.input(POLARIZA_FRENO_OUT_PIN)


        if variables.RUEDA_INICIO == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(RUEDA_INDICE_PIN):
                variables.FIRST_INIT_RUEDA = 1
                variables.RUEDA_INDICE = 1
            else:
                variables.FIRST_INIT_RUEDA = 0
                variables.RUEDA_INDICE = 0

        if variables.POLARIZA_INICIO == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(POLARIZA_INDICE_PIN):
                variables.FIRST_INIT_POLARIZA = 1
                variables.POLARIZA_INDICE = 1
            else:
                variables.FIRST_INIT_POLARIZA = 0
                variables.POLARIZA_INDICE = 0

        if variables.REDUCTOR_ROJO == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(REDUCTOR_ROJO_PIN):
                variables.FIRST_INIT_REDUCTOR = 1
                variables.REDUCTOR_ROJO = 1
                variables.REDUCTOR_INDICE = 2
            else:
                variables.FIRST_INIT_REDUCTOR = 0
                variables.REDUCTOR_ROJO = 0

        if variables.REDUCTOR_AZUL == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(REDUCTOR_AZUL_PIN):
                variables.REDUCTOR_AZUL = 1
                variables.REDUCTOR_INDICE = 1
            else:
                variables.REDUCTOR_AZUL = 0
        '''
        if variables.REDUCTOR_FUERA == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(REDUCTOR_FUERA_PIN):
                variables.REDUCTOR_FUERA = 1
            else:
                variables.REDUCTOR_FUERA = 0
        '''
        if variables.RUEDA_FRENO_SENSOR == 0 or variables.RUEDA_FRENO_SENSOR == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(RUEDA_FRENO_IN_PIN):
                variables.RUEDA_FRENO_SENSOR = 0
            else:
                variables.RUEDA_FRENO_SENSOR = 1

        estado = {
                'RUEDA_INICIO': variables.RUEDA_INICIO,
                'RUEDA_INDICE': variables.RUEDA_INDICE,
                'POLARIZA_INICIO': variables.POLARIZA_INICIO,
                'POLARIZA_INDICE': variables.POLARIZA_INDICE,
                'REDUCTOR_AZUL': variables.REDUCTOR_AZUL,
                'REDUCTOR_ROJO': variables.REDUCTOR_ROJO,
                'REDUCTOR_FUERA': variables.REDUCTOR_FUERA,
                'REDUCTOR_INDICE': variables.REDUCTOR_INDICE,
                'RUEDA_FRENO': variables.RUEDA_FRENO,
                'POLARIZA_FRENO': variables.POLARIZA_FRENO,
                'REDUCTOR_FRENO': variables.REDUCTOR_FRENO,
                'RUEDA_INDICE_SET': variables.RUEDA_INDICE_SET,
                'POLARIZA_INDICE_SET': variables.POLARIZA_INDICE_SET,
                'REDUCTOR_SET': variables.REDUCTOR_SET,
                'RUEDA_PASOS': variables.RUEDA_PASOS,
                'POLARIZA_PASOS': variables.POLARIZA_PASOS,
                'REDUCTOR_PASOS': variables.REDUCTOR_PASOS,
                'FIRST_INIT_RUEDA': variables.FIRST_INIT_RUEDA,
                'FIRST_INIT_POLARIZA': variables.FIRST_INIT_POLARIZA,
                'FIRST_INIT_REDUCTOR': variables.FIRST_INIT_REDUCTOR,
                'RUEDA_FRENO_SENSOR': variables.RUEDA_FRENO_SENSOR,
                'POLARIZA_FRENO_SENSOR': variables.POLARIZA_FRENO_SENSOR,
                'RUEDA_PARO_EMERGENCIA': variables.RUEDA_STOP
                }
        estado_json = json.dumps(estado, separators=(',', ':'), sort_keys=True) #data serialized
        print ("[+] Estado inicial: ")
        print (estado_json)


    def run(self):
        self.initInterrupciones()
        time.sleep(0.2)
        print ("[+] Iniciando Servicio de Interrupciones OK")
        self.initStatus()
        time.sleep(0.2)
        FirstinitPos()



# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread):
    def __init__(self,ip,port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.reductimeout = time.time() + 60*1.20   # 1 minuto desde el inicio
        self.ruedatimeout = time.time() + 14*1.20   # 1 minuto desde el inicio
        self.polarizatimeout = time.time() + 60*1.20   # 1 minuto desde el inicio
        self.completado = 1
        self.pasosextra = 0
        print ("[+] Nuevo server socket thread iniciado desde " + ip + ":" + str(port))
        #self.conn.send(str.encode('Bienvenido '+ ip + ' procesando comando...' + '\n'))  # lo quite por errores en el json


    def run(self):
        #RUEDA_MOTOR bottomhat 1
        #POLARIZA_MOTOR bottomhat 2
        #REDUCTOR_MOTOR tophat 1

        while True:
            data = self.conn.recv(2048).strip()
            if not data:
                print ("Comando Recibido: NO DATA")
                break
            #message_queues[self.conn].put(data)
            data = data.decode('utf-8') # decodificar el mensaje
            data = data.upper() # convertir a mayusculas
            print ("Comando Recibido: " + data)
            datasplit = data.split(' ')
            comando = datasplit[0]
            print (datasplit) # debug

            # Comandos
            if comando == 'RUEDA':           #EJEMPLO: echo RUEDA 1 | nc ip 6666  (del 1 al 8)
                if variables.FIRST_INIT_RUEDA != 1 or variables.RUEDA_STOP == 1:
                    print ("[+] ERROR: RUEDA DE FILTROS NO INICIALIZADA")
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- RUEDA DE FILTROS NO INICIALIZADA -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                variables.RUEDA_INDICE_SET = int(datasplit[1])
                if variables.RUEDA_INDICE_SET >= 1 and variables.RUEDA_INDICE_SET <= 8:
                    rueda_pos = variables.RUEDA_INDICE
                    if rueda_pos == 8:
                        rueda_pos = 0
                    rueda_dif = rueda_pos - variables.RUEDA_INDICE_SET

                    if rueda_dif == -4 or rueda_dif == -3 or rueda_dif == -2 or rueda_dif == -1 or rueda_dif == 4 or rueda_dif == 5 or rueda_dif == 6:
                        GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
                        #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                        time.sleep(1.0)
                        print ("[+] RUEDA: FRENO OFF")
                        #time.sleep(1.0)
                        variables.RUEDA_SENTIDO = 1      #suma contador, ver interrupciones
                        # pruebas de la rampa
                        # RUEDA_MOTOR.setSpeed(80)
                        RUEDA_MOTOR.setSpeed(5)
                        for i in range(5, 81, 1):
                            RUEDA_MOTOR.setSpeed(i)
                            print(i)
                            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                        while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                            #try:
                                #self.conn.send(str.encode('+' + '\n'))  # echo
                            #except BrokenPipeError as e:
                                #pass
                            if time.time() >= self.ruedatimeout:
                                print ("[+] RUEDA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                        turnOffRueda()      # Busca posicion de freno correcta
                        self.completado = 1


                    elif rueda_dif != 0 and rueda_dif != -8:
                        GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
                        #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                        time.sleep(1.0)
                        print ("[+] RUEDA: FRENO OFF")
                        variables.RUEDA_SENTIDO = 0      #resta contador, ver interrupciones
                        # pruebas de la rampa
                        # RUEDA_MOTOR.setSpeed(80)
                        RUEDA_MOTOR.setSpeed(5)
                        for i in range(5, 81, 2):
                            RUEDA_MOTOR.setSpeed(i)
                            print(i)
                            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.RUEDA_PASOS = variables.RUEDA_PASOS - 1
                        while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.RUEDA_PASOS = variables.RUEDA_PASOS - 1
                            #try:
                                #self.conn.send(str.encode('+' + '\n'))  # echo
                            #except BrokenPipeError as e:
                                #pass
                            if time.time() >= self.ruedatimeout:
                                print ("[+] RUEDA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                        time.sleep(0.50)
                        RUEDA_MOTOR.step(80, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS - 80
                        variables.RUEDA_INDICE = variables.RUEDA_INDICE - 1     #resta un contador para regresar en un mismo sentido siempre
                        print (">>Restado 1 en RUEDA_INDICE_PIN para Compensar>>")
                        print ("RUEDA_INDICE = " + str(variables.RUEDA_INDICE))
                        variables.RUEDA_SENTIDO = 1      #suma contador, ver interrupciones
                        time.sleep(0.50)
                        while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                            #try:
                                #self.conn.send(str.encode('+' + '\n'))  # echo
                            #except BrokenPipeError as e:
                                #pass
                            if time.time() >= self.ruedatimeout:
                                print ("[+] RUEDA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                        turnOffRueda()      # Busca posicion de freno correcta
                        self.completado = 1
                        
                    turnOffRueda()
                    time.sleep(0.50)
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                    #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                    print ("[+] RUEDA: FRENO ON")
                    if self.completado == 1:
                        try:
                            self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] OK")
                    elif self.completado == 0:
                        try:
                            self.conn.send(str.encode('ERROR: ' + '-- VERIFICAR SWITCH LIMITE -- ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] ERROR: VERIFICAR SWITCH LIMITE")
                        variables.FIRST_INIT_RUEDA = 0
                    elif self.completado == -1:
                        try:
                            self.conn.send(str.encode('ERROR: ' + '-- FRENO RUEDA NO LLEGO A SU POSICION -- ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] ERROR: FRENO RUEDA NO LLEGO A SU POSICION")
                        variables.FIRST_INIT_RUEDA = 0
                    self.conn.close()
                    break
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break

            #Emergency Stop
            elif comando == 'STOP':
                variables.RUEDA_STOP = 1
                variables.FIRST_INIT_RUEDA = 0
                variables.FIRST_INIT_POLARIZA = 0
                variables.FIRST_INIT_REDUCTOR = 0
                turnOffMotors()
                time.sleep(1.0)
                GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
                print ("[+] PARO DE EMERGENCIA")
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'FRENOS':
                frenosonoff = int(datasplit[1])
                if frenosonoff == 1:
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                    #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
                elif frenosonoff == 0:
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
                    #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
                    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.HIGH)
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break

                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'INICIO':       #VA A INICIO DE POSICION
                initPos()
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'ESTADO':     #REGRESA Estado ACTUAL
                variables.RUEDA_FRENO = GPIO.input(RUEDA_FRENO_OUT_PIN)
                variables.POLARIZA_FRENO = GPIO.input(POLARIZA_FRENO_OUT_PIN)
                variables.REDUCTOR_FRENO = GPIO.input(REDUCTOR_FRENO_OUT_PIN)

                print ("Peticicion del Cliente por Estado: ", data)
                estado = {
                    'RUEDA_INICIO': variables.RUEDA_INICIO,
                    'RUEDA_INDICE': variables.RUEDA_INDICE,
                    'POLARIZA_INICIO': variables.POLARIZA_INICIO,
                    'POLARIZA_INDICE': variables.POLARIZA_INDICE,
                    'REDUCTOR_AZUL': variables.REDUCTOR_AZUL,
                    'REDUCTOR_ROJO': variables.REDUCTOR_ROJO,
                    'REDUCTOR_FUERA': variables.REDUCTOR_FUERA,
                    'REDUCTOR_INDICE': variables.REDUCTOR_INDICE,
                    'RUEDA_FRENO': variables.RUEDA_FRENO,
                    'POLARIZA_FRENO': variables.POLARIZA_FRENO,
                    'REDUCTOR_FRENO': variables.REDUCTOR_FRENO,
                    'RUEDA_INDICE_SET': variables.RUEDA_INDICE_SET,
                    'POLARIZA_INDICE_SET': variables.POLARIZA_INDICE_SET,
                    'REDUCTOR_SET': variables.REDUCTOR_SET,
                    'RUEDA_PASOS': variables.RUEDA_PASOS,
                    'POLARIZA_PASOS': variables.POLARIZA_PASOS,
                    'REDUCTOR_PASOS': variables.REDUCTOR_PASOS,
                    'FIRST_INIT_RUEDA': variables.FIRST_INIT_RUEDA,
                    'FIRST_INIT_POLARIZA': variables.FIRST_INIT_POLARIZA,
                    'FIRST_INIT_REDUCTOR': variables.FIRST_INIT_REDUCTOR,
                    'RUEDA_FRENO_SENSOR': variables.RUEDA_FRENO_SENSOR,
                    'POLARIZA_FRENO_SENSOR': variables.POLARIZA_FRENO_SENSOR,
                    'RUEDA_PARO_EMERGENCIA': variables.RUEDA_STOP
                    }
                estado_json = json.dumps(estado, separators=(',', ':'), sort_keys=True) #data serialized

                try:
                    self.conn.send(str.encode(estado_json + '\n'))
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'NOMBRE':     #REGRESA Nombres de Filtros
                print ("Peticicion del Cliente por Nombres: ", data)
                nombres = {
                    'Filtro01': variables.N_FILTRO_01,
                    'Filtro02': variables.N_FILTRO_02,
                    'Filtro03': variables.N_FILTRO_03,
                    'Filtro04': variables.N_FILTRO_04,
                    'Filtro05': variables.N_FILTRO_05,
                    'Filtro06': variables.N_FILTRO_06,
                    'Filtro07': variables.N_FILTRO_07,
                    'Filtro08': variables.N_FILTRO_08,
                    'Polariza01': variables.N_POLARIZA_01,
                    'Polariza02': variables.N_POLARIZA_02,
                    'Polariza03': variables.N_POLARIZA_03,
                    'Polariza04': variables.N_POLARIZA_04,
                    'Polariza05': variables.N_POLARIZA_05,
                    'Reductor01': variables.N_REDUCTOR_01,
                    'Reductor02': variables.N_REDUCTOR_02,
                    'Reductor03': variables.N_REDUCTOR_03
                    }
                nombres_json = json.dumps(nombres, separators=(',', ':'), sort_keys=True) #data serialized

                try:
                    self.conn.send(str.encode(nombres_json + '\n'))
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'CAMBIO':     #CAMBIA Nombres de Filtros
                print ("Peticicion del Cliente por Cambio de Nombres: ", data)
                nombresjson = data[6:] # fix flx datasplit[1]
                #nombresjson1 = nombresjson.decode('utf-8')    #decodificar el mensaje
                #print(nombresjson)
                nombresjson2 = json.loads(nombresjson)

                if 'FILTRO01' in nombresjson2:
                    variables.N_FILTRO_01 = nombresjson2['FILTRO01']                              #0
                if 'FILTRO02' in nombresjson2:
                    variables.N_FILTRO_02 = nombresjson2['FILTRO02']                              #1
                if 'FILTRO03' in nombresjson2:
                    variables.N_FILTRO_03 = nombresjson2['FILTRO03']                              #2
                if 'FILTRO04' in nombresjson2:
                    variables.N_FILTRO_04 = nombresjson2['FILTRO04']                              #3
                if 'FILTRO05' in nombresjson2:
                    variables.N_FILTRO_05 = nombresjson2['FILTRO05']                              #4
                if 'FILTRO06' in nombresjson2:
                    variables.N_FILTRO_06 = nombresjson2['FILTRO06']                              #5
                if 'FILTRO07' in nombresjson2:
                    variables.N_FILTRO_07 = nombresjson2['FILTRO07']                              #6
                if 'FILTRO08' in nombresjson2:
                    variables.N_FILTRO_08 = nombresjson2['FILTRO08']                              #7

                if 'POLARIZA01' in nombresjson2:
                    variables.N_POLARIZA_01 = nombresjson2['POLARIZA01']                       #0
                if 'POLARIZA02' in nombresjson2:
                    variables.N_POLARIZA_02 = nombresjson2['POLARIZA02']                       #1
                if 'POLARIZA03' in nombresjson2:
                    variables.N_POLARIZA_03 = nombresjson2['POLARIZA03']                       #2
                if 'POLARIZA04' in nombresjson2:
                    variables.N_POLARIZA_04 = nombresjson2['POLARIZA04']                       #3
                if 'POLARIZA05' in nombresjson2:
                    variables.N_POLARIZA_05 = nombresjson2['POLARIZA05']                       #4

                if 'REDUCTOR01' in nombresjson2:
                    variables.N_REDUCTOR_01 = nombresjson2['REDUCTOR01']                          #0
                if 'REDUCTOR02' in nombresjson2:
                    variables.N_REDUCTOR_02 = nombresjson2['REDUCTOR02']                          #1
                if 'REDUCTOR03' in nombresjson2:
                    variables.N_REDUCTOR_03 = nombresjson2['REDUCTOR03']                          #2

                print ("[+] CAMBIO NOMBRES FILTROS OK")

                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'EXIT':
                now = time.strftime('%Y-%m-%d %H:%M')
                print(now + ' - Conexion Terminada por el Cliente')
                try:
                    self.conn.send(str.encode('Recibido: Adios' + '\n'))
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            else:
                now = time.strftime('%Y-%m-%d %H:%M')
                print(now + ' - No Existe el Comando - Conexion Terminada')
                try:
                    self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break



# Programa Principal
try:
    turnOffMotors()
    variables = Ruca2_variables.Rueda()      #Variables
    principal = Principal()
    principal.run()

    print ("[+] SERVIDOR DE LA RUCA 2.0 - RUEDA DE FILTROS Iniciado! Presione CTRL+C para Salir")
    # become a server socket
    tcpServer.listen(7)

    while True:
        print ("Esperando por Conexiones...")
        (conn, (ip, port)) = tcpServer.accept()

        threadSockets = ClientThread(ip, port)
        threadSockets.start()
        threads.append(threadSockets)
        #message_queues[threadSockets] = Queue.Queue()

    tcpServer.shutdown()
    tcpServer.close()
    # wait until worker threads are done to exit
    for t in threads:
        t.join()


except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    turnOffMotors()
    #RUEDA_FRENO_OUT_PWM.stop()
    #POLARIZA_FRENO_OUT_PWM.stop()
    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
    GPIO.cleanup()
    print ("Adios Viajero")
    sys.exit()
    #session.close()
    #session.dispose()
    tcpServer.shutdown()
    tcpServer.close()
