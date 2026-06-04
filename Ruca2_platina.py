#!/usr/bin/env python3

'''
RUCA 2.0 - PLATINA GIRATORIA
Version 0.9-dev          03/Oct/2019
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
2 - Interruptores límite N.A. para filtros (Indice y Posiciones 1-8)
2 - Interruptores límite N.A. para polarizadores (Indice y Posiciones 1-5)
2 - Interruptores límite N.A. para reductores (Indices: Azul, Rojo y Fuera)
2 - Interruptores límite N.A. para platina (Indice, límite, límite duro (sin lectura))

El control esta implementado mediante un código en lenguaje Python 3,
basado en una microcomputadora de la línea Raspberry Pi 3 modelo B.

Comandos que Ejecuta el Servidor:

PLATINA_POS #%POS: va a la posición en porcentaje 0-100 del recorrido de la platina (calibrar antes)
PLATINA_ENC #PULSOS: va a la posición de pulsos de cuadratura indicada
ESTADO: devuelve el estado de las variables en formato json
INICIO: busca inicio de la platina

Funciones Añadidas:

Ver. 0.9 - Platina giratoria fue clausurada en el proyecto, reduje timeouts
Ver. 0.8 - Se agrego timeout de movimientos para evitar sobrecalentamiento de amplificadores en caso de falla
Ver. 0.7 - Entonado control de velocidad
Ver. 0.6 - Se corrigio un bug en la clase de sockets: ahora se usa self.conn en vez de conn para que cada hilo tenga su propio comando
Ver. 0.5 - En Desarrollo - Se definio un modulo independiente con todas las variables
Ver. 0.4 - En Desarrollo - Probando inicialización automática
Ver. 0.3 - En Desarrollo - Falta crear inicialización automática cuando despierta el Roboclaw
Ver. 0.2 - En Desarrollo
Ver. 0.1 - Implementada
'''

#***Before using this example the motor/controller combination must be
#***tuned and the settings saved to the Roboclaw using IonMotion.
#***The Min and Max Positions must be at least 0 and 50000

# Modulos externos
import os
import sys
from threading import Thread
import random
import atexit
import socket
import subprocess
import simplejson as json
import queue as Queue
import time
from pyroboclaw.roboclaw import RoboClaw
import RPi.GPIO as GPIO

import Ruca2_variables



# GPIOS Entradas
PLATINA_INICIO_PIN = 13
PLATINA_FIN_PIN = 26
PLATINA_FRENO_IN_PIN = 8

# GPIOS Salidas
PLATINA_FRENO_OUT_PIN = 20


# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme                    # GPIO pulled down, detecta  3.3V con la interrupcion
GPIO.setwarnings(False)
GPIO.setup(PLATINA_INICIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)       #13  Pull_down
GPIO.setup(PLATINA_FIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)          #26  Pull_down
GPIO.setup(PLATINA_FRENO_IN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #8  Pull_down

GPIO.setup(PLATINA_FRENO_OUT_PIN, GPIO.OUT)                               #20

PLATINA_FRENO_OUT_PWM = GPIO.PWM(PLATINA_FRENO_OUT_PIN, 1000)  # channel=20 frequency=1Hz


#Windows comport name
#rc = Roboclaw("COM3",115200)
#Definimos el roboclaw como un objeto
roboclaw1 = RoboClaw("/dev/ttyS0", 0x80)


# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 7777
BUFFER_SIZE = 2048  # Usually 1024, but we need quick response

# create an INET, STREAMing socket
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind the socket to a public host, and a well-known port
tcpServer.bind((TCP_IP, TCP_PORT))
threads = []
#message_queues = {}

# Funciones normales
# Apaga todos los motores
def turnOffMotors():
    roboclaw1.stop_all()

# Apaga el motor de la Platina
def turnOffPLATINA():
    roboclaw1.stop_motor(motor=1)

# resetea cuenta de encoders
def resetEncoders(number):
    roboclaw1.reset_quad_encoder(number)
    print ("[+] Encoder reseteado del motor: " + str(number))


# recommended for auto-disabling motors on shutdown!
atexit.register(turnOffMotors)



# Envia a posiciones de inicio al ARRANCAR la platina giratoria
def FirstinitPos():
    platinacompletado = 1
    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
    time.sleep(1)
    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
    time.sleep(1)
    print ("[+] PLATINA: FRENO OFF")
    time.sleep(2)

    print ("[+] PLATINA: INICIO BUSCANDO...")
    platinatimeout = time.time() + 60*1.50   # 1 minuto desde el inicio
    roboclaw1.backward_motor(motor=1)
    while variables.FIRST_INIT_PLATINA != 1:
        print ("-")
        time.sleep(0.001)
        if time.time() >= platinatimeout:
            platinacompletado = 0
            break

    turnOffPLATINA()
    time.sleep(0.5)
    roboclaw1.forward_motor(motor=1)      # prueba para salir del switch
    time.sleep(0.5)
    turnOffPLATINA()
    if platinacompletado == 1:
        print ("[+] PLATINA: INICIO ENCONTRADO!")
        time.sleep(0.2)
        #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
        PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
        time.sleep(1)
        PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
        time.sleep(1)
        print ("[+] PLATINA: FRENO OFF")
        time.sleep(2)

        roboclaw1.drive_to_position_raw(motor=1, accel=200, speed=700, deccel=200, position=0, buffer=1)
        #roboclaw1.drive_to_position(motor=1, accel=5000, speed=20000, deccel=5000, position=0, buffer=1)
        variables.PLATINA_ENC = roboclaw1.read_encoder(1)
        while variables.PLATINA_ENC >= (0 + variables.PLATINA_DEAD_ZONE) or variables.PLATINA_ENC <= (0 - variables.PLATINA_DEAD_ZONE):
            variables.PLATINA_ENC = roboclaw1.read_encoder(1)
            print (variables.PLATINA_ENC)
            time.sleep(0.2)

        print ("[+] PLATINA: POSICION INICIO OK")
        variables.PLATINA_SET = 0
        time.sleep(2)
        #turnOffPLATINA()
        #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
        PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
        print ("[+] PLATINA: FRENO ON")
        time.sleep(2)
    else:
        print ("[+] ERROR: VERIFICAR SWITCH DE INICIO")
        #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
        PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
        time.sleep(2)


# Envia a posiciones de inicio la platina giratoria
def initPos():
    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
    print ("[+] PLATINA: FRENO OFF")
    print ("[+] Iniciando Platina...")
    variables.FIRST_INIT_PLATINA = 0    # desconoce la inicializada anterior
    time.sleep(0.2)
    principal = Principal()
    principal.initStatus()
    time.sleep(0.2)
    FirstinitPos()
    print ("[+] Inicializada Rueda de Filtros OK")


#Clase Principal
class Principal():
    def __init__(self):
        PLATINA_FRENO_OUT_PWM.start(0)
        #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
        print ("[+] Variables de la Platina Giratoria Cargadas")


        # Funciones Callback
        # these will run in another thread when our events are detected
    def PLATINA_inicio(self, channel):
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(PLATINA_INICIO_PIN):
            variables.PLATINA_INICIO = 1
            variables.FIRST_INIT_PLATINA = 1
            print (">>rising edge detectado en PLATINA_INICIO_PIN>>")
            resetEncoders(number=1)
            print ("[+] SWITCH LIMITE: PLATINA_INICIO")
            #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
            #print ("[+] PLATINA: FRENO OFF")
        else:
            variables.PLATINA_INICIO = 0
            print ("<<falling edge detectado on PLATINA_INICIO_PIN<<")


    def PLATINA_fin(self, channel):
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(PLATINA_FIN_PIN):
            variables.PLATINA_FIN = 1
            print (">>rising edge detectado on PLATINA_FIN_PIN>>")
            turnOffPLATINA()
            #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
            PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
            print ("[+] SWITCH LIMITE: PLATINA_FIN")
            print ("[+] PLATINA: MOTOR OFF")
            print ("[+] PLATINA: FRENO OFF")
        else:
            variables.PLATINA_FIN = 0
            print ("<<falling edge detectado on PLATINA_FIN_PIN<<")


    def PLATINA_sensor(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(PLATINA_FRENO_IN_PIN):
            variables.PLATINA_FRENO_SENSOR = 1
            print (">>rising edge detected on PLATINA_FRENO_IN_PIN>>")
        else:
            variables.PLATINA_FRENO_SENSOR = 0
            print ("<<falling edge detected on PLATINA_FRENO_IN_PIN<<")


    # Detectamos interrupciones
    def initInterrupciones(self):
        # when a rising edge is detected on gpio, regardless of whatever
        # else is happening in the program, the function my_callback will be run
        GPIO.add_event_detect(PLATINA_INICIO_PIN, GPIO.BOTH, callback=self.PLATINA_inicio, bouncetime=200)
        GPIO.add_event_detect(PLATINA_FIN_PIN, GPIO.BOTH, callback=self.PLATINA_fin, bouncetime=200)
        GPIO.add_event_detect(PLATINA_FRENO_IN_PIN, GPIO.BOTH, callback=self.PLATINA_sensor, bouncetime=200)


    # Estado inicial de los interruptores
    def initStatus(self):
        variables.PLATINA_INICIO = GPIO.input(PLATINA_INICIO_PIN)             #13
        variables.PLATINA_FIN = GPIO.input(PLATINA_FIN_PIN)                   #26
        variables.PLATINA_FRENO = GPIO.input(PLATINA_FRENO_OUT_PIN)         #20
        variables.PLATINA_FRENO_SENSOR = GPIO.input(PLATINA_FRENO_IN_PIN)   #8
        variables.PLATINA_SET = 0
        resetEncoders(number=1) #resetea encoder al inicio
        variables.PLATINA_ENC = roboclaw1.read_encoder(1)
        variables.PLATINA_POS = roboclaw1.read_position(1)
        variables.PLATINA_MIN = roboclaw1.read_range(1)[0]
        variables.PLATINA_MAX = roboclaw1.read_range(1)[1]
        variables.TEMP_ROBO_1 = roboclaw1.read_temp_sensor(1)

        if variables.PLATINA_INICIO == 1:
            time.sleep(0.005) # debounce for 5mSec
            if GPIO.input(PLATINA_INICIO_PIN):
                variables.FIRST_INIT_PLATINA = 1
            else:
                variables.FIRST_INIT_PLATINA = 0

        estado = {
                'PLATINA_INICIO': variables.PLATINA_INICIO,
                'PLATINA_FIN': variables.PLATINA_FIN,
                'PLATINA_ENC': variables.PLATINA_ENC,
                'PLATINA_POS': variables.PLATINA_POS,
                'PLATINA_SET': variables.PLATINA_SET,
                'PLATINA_MIN': variables.PLATINA_MIN,
                'PLATINA_MAX': variables.PLATINA_MAX,
                'PLATINA_FRENO': variables.PLATINA_FRENO,
                'TEMP_ROBO_1': variables.TEMP_ROBO_1,
                'FIRST_INIT_PLATINA': variables.FIRST_INIT_PLATINA,
                'PLATINA_FRENO_SENSOR': variables.PLATINA_FRENO_SENSOR
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
        self.platinatimeout = time.time() + 60*1   # 1 minuto desde el inicio
        self.completado = 1
        print ("[+] Nuevo server socket thread iniciado desde " + ip + ":" + str(port))
        #self.conn.send(str.encode('Bienvenido '+ ip + ' procesando comando...' + '\n'))    # lo quite por errores en el json


    def run(self):

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
            print (datasplit) ##debug

            # Comandos
            # manda a posicion de rango (0-100%)
            if comando == 'PLATINA_POS':        #EJEMPLO: echo PLATINA_POS 0-100 | nc ip 7777 (del 0 al 99999999)
                if variables.FIRST_INIT_PLATINA != 1:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- MECANISMO DE PLATINA NO INICIALIZADO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                variables.PLATINA_SET = int(datasplit[1])

                if variables.PLATINA_FIN == 0 and variables.PLATINA_SET >=0:
                    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    time.sleep(1)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
                    time.sleep(1)
                    print ("[+] PLATINA: FRENO OFF")
                    time.sleep(2)

                    roboclaw1.drive_to_position(motor=1, accel=200, speed=700, deccel=200, position=variables.PLATINA_SET, buffer=1)
                    #roboclaw1.drive_to_position(motor=1, accel=0, speed=0, deccel=0, position=variables.PLATINA_SET, buffer=1)

                    variables.PLATINA_POS = roboclaw1.read_position(1)
                    while variables.PLATINA_POS >= (variables.PLATINA_SET + 0.55) or variables.PLATINA_POS <= (variables.PLATINA_SET - 0.55):
                        variables.PLATINA_POS = roboclaw1.read_position(1)
                        print (variables.PLATINA_POS)
                        try:
                            self.conn.send(str.encode('+' + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        time.sleep(0.20)
                        if time.time() >= self.platinatimeout:
                            self.completado = 0
                            break

                time.sleep(2)
                #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                print ("[+] PLATINA: FRENO ON")
                if self.completado == 1:
                    try:
                        self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print ("[+] OK")
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- VERIFICAR MOTOR PLATINA -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print ("[+] ERROR: VERIFICAR MOTOR PLATINA")
                self.conn.close()
                break


            # manda a posicion de cuentas de encoder
            elif comando == 'PLATINA_ENC':        #EJEMPLO: echo PLATINA_ENC 1000(pulsos) | nc ip 7777 (del 0 al 99999999)
                if variables.FIRST_INIT_PLATINA != 1:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- MECANISMO DE PLATINA NO INICIALIZADO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                variables.PLATINA_SET = int(datasplit[1])

                if variables.PLATINA_FIN == 0 and variables.PLATINA_SET >=0:
                    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    time.sleep(1)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
                    time.sleep(1)
                    print ("[+] PLATINA: FRENO OFF")
                    time.sleep(2)

                    roboclaw1.drive_to_position_raw(motor=1, accel=200, speed=700, deccel=200, position=variables.PLATINA_SET, buffer=1)
                    #roboclaw1.drive_to_position_raw(motor=1, accel=0, speed=0, deccel=0, position=variables.PLATINA_SET, buffer=1)

                    variables.PLATINA_ENC = roboclaw1.read_encoder(1)
                    while variables.PLATINA_ENC >= (variables.PLATINA_SET + variables.PLATINA_DEAD_ZONE) or variables.PLATINA_ENC <= (variables.PLATINA_SET - variables.PLATINA_DEAD_ZONE):
                        variables.PLATINA_ENC = roboclaw1.read_encoder(1)
                        print (variables.PLATINA_ENC)
                        try:
                            self.conn.send(str.encode('+' + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        time.sleep(0.20)
                        if time.time() >= self.platinatimeout:
                            self.completado = 0
                            break

                time.sleep(2)
                #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                print ("[+] PLATINA: FRENO ON")
                if self.completado == 1:
                    try:
                        self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print ("[+] OK")
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- VERIFICAR MOTOR PLATINA -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print ("[+] ERROR: VERIFICAR MOTOR PLATINA")
                self.conn.close()
                break


            # Busca inicio el motor
            elif comando == 'INICIO':       #VA A INICIO DE POSICION, EJEMPLO: INICIO PLATINA
                initPos()
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            # mueve hacia adelante a media velocidad
            elif comando == 'FORWARD':        #EJEMPLO: echo FORWARD PLATINA | nc ip 7777
                motor = str(datasplit[1])
                GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
                time.sleep(2)

                if motor == "PLATINA":
                    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    time.sleep(1)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
                    time.sleep(1)
                    roboclaw1.forward_motor(motor=1)
                    print ("Forward PLATINA")
                    time.sleep(5)

                else:
                    turnOffMotors()
                    time.sleep(0.1)
                    break

                turnOffMotors()
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            # mueve hacia atras a media velocidad
            elif comando == 'BACKWARD':        #EJEMPLO: echo BACKWARD PLATINA | nc ip 7777
                motor = str(datasplit[1])
                GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
                time.sleep(2)

                if motor == "PLATINA":
                    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    time.sleep(1)
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
                    time.sleep(1)
                    roboclaw1.backward_motor(motor=1)
                    print ("Backward PLATINA")
                    time.sleep(5)

                else:
                    turnOffMotors()
                    time.sleep(0.1)
                    break

                turnOffMotors()
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            # mueve hacia atras a media velocidad
            elif comando == 'TEST':        #EJEMPLO: echo TEST PLATINA | nc ip 7777
                motor = str(datasplit[1])
                #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.HIGH)
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                time.sleep(1)
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(70)
                time.sleep(1)

                if motor == "PLATINA":
                    for i in range(5):
                        roboclaw1.forward_motor(motor=1)
                        print ("Forward PLATINA")
                        time.sleep(3.5)

                        roboclaw1.backward_motor(motor=1)
                        print ("Backward PLATINA")
                        time.sleep(3.5)

                else:
                    turnOffMotors()
                    break

                turnOffMotors()
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'ESTADO':     #REGRESA Estado ACTUAL
                variables.PLATINA_INICIO = GPIO.input(PLATINA_INICIO_PIN)     #13
                variables.PLATINA_FIN = GPIO.input(PLATINA_FIN_PIN)           #26
                variables.PLATINA_FRENO = GPIO.input(PLATINA_FRENO_OUT_PIN)       #20
                variables.PLATINA_SET = variables.PLATINA_SET
                variables.PLATINA_ENC = roboclaw1.read_encoder(1)
                variables.PLATINA_POS = roboclaw1.read_position(1)
                variables.PLATINA_MIN = roboclaw1.read_range(1)[0]
                variables.PLATINA_MAX = roboclaw1.read_range(1)[1]
                variables.TEMP_ROBO_1 = roboclaw1.read_temp_sensor(1)

                print ("Peticicion del Cliente por Estado: ", data)
                estado = {
                    'PLATINA_INICIO': variables.PLATINA_INICIO,
                    'PLATINA_FIN': variables.PLATINA_FIN,
                    'PLATINA_ENC': variables.PLATINA_ENC,
                    'PLATINA_POS': variables.PLATINA_POS,
                    'PLATINA_SET': variables.PLATINA_SET,
                    'PLATINA_MIN': variables.PLATINA_MIN,
                    'PLATINA_MAX': variables.PLATINA_MAX,
                    'PLATINA_FRENO': variables.PLATINA_FRENO,
                    'TEMP_ROBO_1': variables.TEMP_ROBO_1,
                    'FIRST_INIT_PLATINA': variables.FIRST_INIT_PLATINA,
                    'PLATINA_FRENO_SENSOR': variables.PLATINA_FRENO_SENSOR
                    }
                estado_json = json.dumps(estado, separators=(',', ':'), sort_keys=True) #data serialized

                try:
                    self.conn.send(str.encode(estado_json + '\n'))
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'STOP':
                turnOffPLATINA()
                print ("[+] PLATINA: MOTOR OFF")
                #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
                PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'FRENOS':
                frenosonoff = int(datasplit[1])
                if frenosonoff == 1:
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                elif frenosonoff == 0:
                    PLATINA_FRENO_OUT_PWM.ChangeDutyCycle(100)
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
                    self.conn.send(str.encode('Adios' + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break




# Programa Principal
try:
    turnOffMotors()
    variables=Ruca2_variables.Platina()      #Variables
    principal = Principal()
    principal.run()

    print ("[+] SERVIDOR DE LA RUCA 2.0 - PLATINA GIRATORIA Iniciado! Presione CTRL+C para Salir")
    # become a server socket
    tcpServer.listen(5)

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
    PLATINA_FRENO_OUT_PWM.stop()
    #GPIO.output(PLATINA_FRENO_OUT_PIN, GPIO.LOW)
    GPIO.cleanup()
    print ("Adios Viajero")
    sys.exit()
    tcpServer.shutdown()
    tcpServer.close()
