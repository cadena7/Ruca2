#!/usr/bin/env python3

'''
RUCA 2.0 - RUEDA DE FILTROS
Version 2.2-dev          5/Junio/2026
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

REDUCTOR (1-3): mete el reductor azul (1) o reductor rojo (2) y lo saca (3)
RUEDA (1-8): va hacia el número de filtro indicado
POLARIZA (1-5): va hacia el número de polarizador indicado
ESTADO: devuelve el estado de las variables en formato json
INICIO: busca inicio de los motores de paso
SPEED: ajusta velocidad de giro del motor de paso en RPM
STOP: detiene los movimientos y bloquea la rueda, para recuperar ejecutar el comando INICIO
FRENOS: libera o mete frenos energizando los solenoides

Ejemplos:
echo RUEDA 2 | nc 192.168.0.34 6666
echo REDUCTOR 3 | nc 192.168.0.34 6666
echo ESTADO | nc 192.168.0.34 6666
echo INICIO | nc 192.168.0.34 6666
echo NOMBRE | nc 192.168.0.34 6666
echo SPEED 80 | nc 192.168.0.34 6666
echo MUEVE 1 100 1 | nc 192.168.0.34 6666           #(echo MUEVE MOTOR(1-2-3) #STEPS DIR(1/0) | nc ip 6666)
echo STOP | nc 192.168.0.34 6666
echo FRENOS 0 | nc 192.168.0.34 6666        #libera frenos

Funciones Añadidas:

Ver. 2.2 - Se agrego lock global para rechazar comandos concurrentes de movimiento e inicializacion cuando la RUCA esta ocupada
Ver. 2.1 - Se agrego control por botones GPIO B_START, B_STOP, B_UP y B_DOWN usando socket local y se añadieron sus variables al estado JSON
Ver. 2.0 - Fix memory leak de threads en sockets
Ver. 1.9 - Ahora el programa se reinicia diario a las 9:00 AM, entonces los filtros para que no se pierdan se almacenan en un archivo JSON
Ver. 1.8 - Elimine el taca-taca de la inicializacion
Ver. 1.7 - La rueda ahora solo gira en un sentido para ver si esto corrije la repetitibilidad
Ver. 1.6 - Añadi comando SPEED para cambiar velocidad de rueda al vuelo, añadi flags de estado RUEDA_SWITCH Y RUEDA_ESTADO
Ver. 1.5 - Sugerencia de Chico de dar el OK justo al leer el switch de indice y no esperar al freno
Ver. 1.4 - Cambio de time.sleep(0.60) a time.sleep(1.0) y los de time.sleep(0.30) a time.sleep(0.50) y los de time.sleep(0.40) a time.sleep(1.0)
Ver. 1.3 - Aumento de velocidad de motores de paso de 20RPM a 60RPM y reducción de time.sleep(2.0) a time.sleep(1.0)
Ver. 1.2 - Correccion de bug en diccionario JSON para cambiar Nombres de Filtros
Ver. 1.1 - Correccion de bug en la funcion de STOP
Ver. 1.0 - Reduje velocidad de motores de rueda de pasos, deje todo listo para habilitar la segunda rueda
Ver. 0.9 - La rueda solo llega de un mismo lado para aumentar repetibilidad, se activaron frenos de solenoides y lectura de su estado
Ver. 0.8 - Se agrego timeout de movimientos para evitar sobrecalentamiento de amplificadores en caso de falla
Ver. 0.7 - Se agrego un algoritmo de decisión el cual determina el sentido apropiado de giro de la rueda para llegar más rapido
Ver. 0.6 - Se corrigio un bug en la clase de sockets: ahora se usa self.conn en vez de conn para que cada hilo tenga su propio comando
Ver. 0.5 - Se definio un modulo independiente con todas las variables
Ver. 0.4 - Agregar base de datos con nombre de filtros
Ver. 0.3 - Falta desarrollar inicializacion
Ver. 0.2 - En Desarrollo
Ver. 0.1 - Implementada
'''

# Modulos externos
from Adafruit_MotorHAT.Adafruit_MotorHAT_Motors import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor
import RPi.GPIO as GPIO
import time
import atexit
import os
import sys
from threading import Thread, Lock
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

B_START_PIN = 7 #IN01
B_STOP_PIN = 21 #IN02
B_UP_PIN = 9    #IN03  
B_DOWN_PIN = 10 #IN04

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

GPIO.setup(B_START_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    #7    Pull_down
GPIO.setup(B_STOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #21   Pull_down
GPIO.setup(B_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)       #9    Pull_down
GPIO.setup(B_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #10   Pull_down

GPIO.setup(RUEDA_FRENO_OUT_PIN, GPIO.OUT)                                #23
GPIO.setup(POLARIZA_FRENO_OUT_PIN, GPIO.OUT)                             #12
GPIO.setup(REDUCTOR_FRENO_OUT_PIN, GPIO.OUT)                             #16

#RUEDA_FRENO_OUT_PWM = GPIO.PWM(RUEDA_FRENO_OUT_PIN, 1000)  # channel=23 frequency=1Hz
#POLARIZA_FRENO_OUT_PWM = GPIO.PWM(POLARIZA_FRENO_OUT_PIN, 1000)  # channel=12 frequency=1Hz

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 6666
BUFFER_SIZE = 2048  # Usually 1024, but we need quick response
RUCA_LOCAL = "nc localhost 6666"
B_START_LOCK = Lock()
B_STOP_LOCK = Lock()
B_MOVE_LOCK = Lock()
COMANDO_MOV_LOCK = Lock()
COMANDOS_MOVIMIENTO = ('REDUCTOR', 'RUEDA', 'POLARIZA', 'MUEVE', 'FRENOS', 'INICIO')

# create an INET, STREAMing socket
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind the socket to a public host, and a well-known port
tcpServer.bind((TCP_IP, TCP_PORT))
#threads = []
#message_queues = {}


# ADAFRUIT MOTORHATS
# bottom hat is default address 0x60
bottomhat = Adafruit_MotorHAT(addr=0x60)
# top hat has A0 jumper closed, so its address 0x61
tophat = Adafruit_MotorHAT(addr=0x61)

RUEDA_MOTOR = bottomhat.getStepper(200, 1)      # 200 steps/rev, motor port #1
POLARIZA_MOTOR = tophat.getStepper(200, 2)      # 200 steps/rev, motor port #2
REDUCTOR_MOTOR = tophat.getStepper(200, 1)      # 200 steps/rev, motor port #1

RUEDA_MOTOR.setSpeed(80)                            # 80 RPM
POLARIZA_MOTOR.setSpeed(80)                         # 80 RPM
REDUCTOR_MOTOR.setSpeed(200)                        # 200 RPM

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    tophat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def turnOffRueda():
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)

def turnOffPolariza():
    tophat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def turnOffReductor():
    tophat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    tophat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)


# recommended for auto-disabling motors on shutdown!
atexit.register(turnOffMotors)



# Envia a posiciones de inicio al ARRANCAR la rueda de filtros y rueda de polarizadores
def FirstinitPos():
    reduccompletado = 1
    ruedacompletado = 1
    polarizacompletado = 1
    ruedapasosextra = 0
    polarizapasosextra = 0
    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
    print ("[+] RUEDA: FRENO OFF")
    time.sleep(1.0)
    print ("[+] INICIANDO Rueda de Filtros")
    variables.RUEDA_ESTADO = "Iniciando RUCA"
    ruedatimeout = time.time() + 60*1.00   # 1 minuto desde el inicio
    while variables.FIRST_INIT_RUEDA != 1:
        RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
        if variables.RUEDA_FRENO_SENSOR == 1:   # Se agrego protección por el nuevo sistema de freno mecánico
            turnOffRueda()
            GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
            print ("[+] ERROR: FRENO NO SE DESACTIVO -- RUEDA: FRENO ON")
            ruedacompletado = -1
            break
        if time.time() >= ruedatimeout:
            ruedacompletado = 0
            break
        #print ("RUEDA_MOTOR+")
        #time.sleep(0.05)
    turnOffRueda()      # Busca posicion de freno correcta
    time.sleep(0.50)
    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
    print ("[+] RUEDA: FRENO ON")
    '''
    time.sleep(1.0)
    
    while ruedapasosextra < 15 and ruedacompletado != 0:
        ruedapasosextra += 1
        time.sleep(1.0)
        if variables.RUEDA_FRENO_SENSOR == 0:
            GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
            time.sleep(1.0)
            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
            variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
            GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
            print ("[+] RUEDA: PASO EXTRA")
            ruedacompletado = -1
        elif variables.RUEDA_FRENO_SENSOR == 1:
            if variables.FIRST_INIT_RUEDA == 0:
                ruedacompletado = -1
            else:
                ruedacompletado = 1
            turnOffRueda()
            print ("[+] RUEDA: FRENO ON")
            break
        if time.time() >= ruedatimeout:
            print ("[+] RUEDA: TIMEOUT")
            ruedacompletado = 0
            break
    turnOffRueda()
    '''
    if ruedacompletado == 1:
        print ("[+] Rueda de Filtros INICIALIZADA OK")
        variables.RUEDA_ESTADO = "RUEDA INICIALIZADA"
    elif ruedacompletado == 0:
        print ("[+] ERROR: VERIFICAR SWITCH LIMITE")
        variables.RUEDA_ESTADO = "ERROR: NO LLEGO FILTRO - VERIFICAR SWITCH"
    elif ruedacompletado == -1:
        print ("[+] ERROR: FRENO RUEDA NO LLEGO A SU POSICION")
        variables.RUEDA_ESTADO = "ERROR: NO ENTRO EL FRENO"

    '''
    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
    time.sleep(1.0)
    print ("[+] INICIANDO Rueda de Polarizadores")
    polarizatimeout = time.time() + 60*1.00   # 1 minuto desde el inicio
    while variables.FIRST_INIT_POLARIZA != 1:
        POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
        #POLARIZA_MOTOR.oneStep(Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.SINGLE)
        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
        if variables.POLARIZA_FRENO_SENSOR == 1:   # Se agrego protección por el nuevo sistema de freno mecánico
            turnOffPolariza()
            GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
            #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
            print ("[+] ERROR: FRENO NO SE DESACTIVO -- POLARIZA: FRENO ON")
            polarizacompletado = -1
            break
        if time.time() >= polarizatimeout:
            polarizacompletado = 0
            break
        #print ("POLARIZA_MOTOR+")
        #time.sleep(0.05)
    turnOffPolariza()      # Busca posicion de freno correcta
    time.sleep(0.50)
    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
    time.sleep(1.0)
    while polarizapasosextra < 15 and polarizacompletado != 0:
        polarizapasosextra += 1
        time.sleep(1.0)
        if variables.POLARIZA_FRENO_SENSOR == 0:
            GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
            #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
            time.sleep(1.0)
            POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
            variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
            GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
            #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
            print ("[+] POLARIZA: PASO EXTRA")
            polarizacompletado = -1
        elif variables.POLARIZA_FRENO_SENSOR == 1:
            if variables.FIRST_INIT_POLARIZA == 0:
                polarizacompletado = -1
            else:
                polarizacompletado = 1
            turnOffPolariza()
            print ("[+] POLARIZA: FRENO ON")
            break
        if time.time() >= polarizatimeout:
            print ("[+] POLARIZA: TIMEOUT")
            polarizacompletado = 0
            break
    turnOffPolariza()
    if polarizacompletado == 1:
        print ("[+] Rueda de Polarizadores INICIALIZADA OK")
    elif polarizacompletado == 0:
        print ("[+] ERROR: VERIFICAR SWITCH LIMITE")
    elif polarizacompletado == -1:
        print ("[+] ERROR: FRENO POLARIZA NO LLEGO A SU POSICION")
    '''

    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.HIGH)
    time.sleep(1.0)
    print ("[+] INICIANDO Reductor Rojo")
    variables.RUEDA_ESTADO = "Iniciando Reductores"
    reductimeout = time.time() + 60*1.00   # 1 minuto desde el inicio
    while variables.FIRST_INIT_REDUCTOR != 1:      #switch normalmente abierto, mover el motor hasta activar el bit accionando el switch n.o.
        REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
        variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS - 10
        if time.time() >= reductimeout:
            print ("[+] REDUCTOR: TIMEOUT")
            reduccompletado = 0
            break
        #print ("REDUCTOR-")
        #time.sleep(0.05)
    turnOffReductor()
    time.sleep(0.50)
    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
    if reduccompletado == 1:
        variables.RUEDA_ESTADO = "REDUCTOR INICIALIZADO"
        print ("[+] Reductor Rojo OK")
    else:
        variables.RUEDA_ESTADO = "ERROR: NO LLEGO REDUCTOR - VERIFICAR SWITCH DE POSICION"
        print ("[+] ERROR: VERIFICAR SWITCH LIMITE")
    time.sleep(0.30)
    if reduccompletado == 1 and ruedacompletado == 1:
        variables.RUEDA_ESTADO = "LISTO"
    time.sleep(0.30)


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
    time.sleep(0.30)
    principal = Principal()
    principal.initStatus()
    time.sleep(0.30)
    FirstinitPos()
    print ("[+] Inicializada Rueda de Filtros OK")


def mandaComandoLocal(comando):
    proceso = subprocess.Popen(RUCA_LOCAL, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    salida, error = proceso.communicate(str.encode(comando))
    proceso.kill()
    if salida:
        print ("[+] RESPUESTA " + comando + ": " + salida.decode('utf-8', 'ignore').strip())
    if error:
        print ("[+] ERROR " + comando + ": " + error.decode('utf-8', 'ignore').strip())


def ejecutaBStart():
    if not B_START_LOCK.acquire(False):
        print ("[+] B_START ignorado: STOP + INICIO en proceso")
        return
    try:
        print ("[+] B_START solicitando STOP")
        mandaComandoLocal("STOP")
        print ("[+] B_START solicitando INICIO")
        mandaComandoLocal("INICIO")
    finally:
        B_START_LOCK.release()


def ejecutaBStop():
    if not B_STOP_LOCK.acquire(False):
        print ("[+] B_STOP ignorado: STOP en proceso")
        return
    try:
        print ("[+] B_STOP solicitando STOP")
        mandaComandoLocal("STOP")
    finally:
        B_STOP_LOCK.release()


def ejecutaBMove(delta):
    if not B_MOVE_LOCK.acquire(False):
        print ("[+] B_UP/B_DOWN ignorado: movimiento de rueda en proceso")
        return
    try:
        filtro_actual = variables.RUEDA_INDICE
        if filtro_actual < 1 or filtro_actual > 8:
            print ("[+] B_UP/B_DOWN ignorado: posicion actual de rueda no valida")
            return
        filtro_destino = filtro_actual + delta
        if filtro_destino > 8:
            filtro_destino = 1
        elif filtro_destino < 1:
            filtro_destino = 8
        comando = "RUEDA " + str(filtro_destino)
        print ("[+] B_UP/B_DOWN solicitando " + comando)
        mandaComandoLocal(comando)
    finally:
        B_MOVE_LOCK.release()


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
            variables.RUEDA_SWITCH = 1
            print (">>rising edge detected on RUEDA_INDICE_PIN>>")
            print ("RUEDA_SWITCH = " + str(variables.RUEDA_SWITCH))
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
            print ("RUEDA_INDICE = " + str(variables.RUEDA_INDICE))
        else:
            variables.RUEDA_SWITCH = 0
            print ("<<falling edge detected on RUEDA_INDICE_PIN<<")
            print ("RUEDA_SWITCH = " + str(variables.RUEDA_SWITCH))
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
            print (">>rising edge detected on POLARIZA_INDICE_PIN>>")
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
            print ("POLARIZA_INDICE = " + str(variables.POLARIZA_INDICE))
        else:
            print ("<<falling edge detected on POLARIZA_INDICE_PIN<<")
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


    def boton_start(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(B_START_PIN):
            variables.B_START = 1
            print (">>rising edge detected on B_START_PIN>>")
            print ("B_START = " + str(variables.B_START))
            threadBotonStart = Thread(target=ejecutaBStart)
            threadBotonStart.daemon = True
            threadBotonStart.start()
        else:
            variables.B_START = 0
            print ("<<falling edge detected on B_START_PIN<<")
            print ("B_START = " + str(variables.B_START))


    def boton_stop(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(B_STOP_PIN):
            variables.B_STOP = 1
            print (">>rising edge detected on B_STOP_PIN>>")
            print ("B_STOP = " + str(variables.B_STOP))
            threadBotonStop = Thread(target=ejecutaBStop)
            threadBotonStop.daemon = True
            threadBotonStop.start()
        else:
            variables.B_STOP = 0
            print ("<<falling edge detected on B_STOP_PIN<<")
            print ("B_STOP = " + str(variables.B_STOP))


    def boton_up(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(B_UP_PIN):
            variables.B_UP = 1
            print (">>rising edge detected on B_UP_PIN>>")
            print ("B_UP = " + str(variables.B_UP))
            threadBotonUp = Thread(target=ejecutaBMove, args=(1,))
            threadBotonUp.daemon = True
            threadBotonUp.start()
        else:
            variables.B_UP = 0
            print ("<<falling edge detected on B_UP_PIN<<")
            print ("B_UP = " + str(variables.B_UP))


    def boton_down(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce for 5mSec
        if GPIO.input(B_DOWN_PIN):
            variables.B_DOWN = 1
            print (">>rising edge detected on B_DOWN_PIN>>")
            print ("B_DOWN = " + str(variables.B_DOWN))
            threadBotonDown = Thread(target=ejecutaBMove, args=(-1,))
            threadBotonDown.daemon = True
            threadBotonDown.start()
        else:
            variables.B_DOWN = 0
            print ("<<falling edge detected on B_DOWN_PIN<<")
            print ("B_DOWN = " + str(variables.B_DOWN))


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
        GPIO.add_event_detect(RUEDA_INDICE_PIN, GPIO.BOTH, callback=self.rueda_indice, bouncetime=200) #RISING antes del 2024 julio
        GPIO.add_event_detect(POLARIZA_INICIO_PIN, GPIO.BOTH, callback=self.polariza_inicio, bouncetime=200)
        GPIO.add_event_detect(POLARIZA_INDICE_PIN, GPIO.BOTH, callback=self.polariza_indice, bouncetime=200)
        GPIO.add_event_detect(REDUCTOR_AZUL_PIN, GPIO.BOTH, callback=self.reductor_azul, bouncetime=200)
        GPIO.add_event_detect(REDUCTOR_ROJO_PIN, GPIO.BOTH, callback=self.reductor_rojo, bouncetime=200)
        #GPIO.add_event_detect(REDUCTOR_FUERA_PIN, GPIO.BOTH, callback=self.reductor_fuera, bouncetime=200)
        GPIO.add_event_detect(RUEDA_FRENO_IN_PIN, GPIO.BOTH, callback=self.rueda_sensor, bouncetime=200)
        GPIO.add_event_detect(POLARIZA_FRENO_IN_PIN, GPIO.BOTH, callback=self.polariza_sensor, bouncetime=200)
        GPIO.add_event_detect(B_START_PIN, GPIO.BOTH, callback=self.boton_start, bouncetime=200)
        GPIO.add_event_detect(B_STOP_PIN, GPIO.BOTH, callback=self.boton_stop, bouncetime=200)
        GPIO.add_event_detect(B_UP_PIN, GPIO.BOTH, callback=self.boton_up, bouncetime=200)
        GPIO.add_event_detect(B_DOWN_PIN, GPIO.BOTH, callback=self.boton_down, bouncetime=200)
        print ("[+] Interrupciones de la Rueda de Filtros Cargadas")


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
        variables.RUEDA_SWITCH = GPIO.input(RUEDA_INDICE_PIN)
        variables.B_START = GPIO.input(B_START_PIN)
        variables.B_STOP = GPIO.input(B_STOP_PIN)
        variables.B_UP = GPIO.input(B_UP_PIN)
        variables.B_DOWN = GPIO.input(B_DOWN_PIN)

        speed = variables.RUEDA_SPEED
        RUEDA_MOTOR.setSpeed(speed)

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
                'RUEDA_PARO_EMERGENCIA': variables.RUEDA_STOP,
                'RUEDA_SWITCH': variables.RUEDA_SWITCH,
                'RUEDA_ESTADO': variables.RUEDA_ESTADO,
                'RUEDA_SPEED': variables.RUEDA_SPEED,
                'B_START': variables.B_START,
                'B_STOP': variables.B_STOP,
                'B_UP': variables.B_UP,
                'B_DOWN': variables.B_DOWN
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
    def __init__(self, ip, port, conn):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.reductimeout = time.time() + 60*1.00   # 1 minuto desde el inicio
        self.ruedatimeout = time.time() + 60*1.00   # 1 minuto desde el inicio
        self.polarizatimeout = time.time() + 60*1.00   # 1 minuto desde el inicio
        self.completado = 1
        self.pasosextra = 0
        self.comando_mov_lock_adquirido = False
        print ("[+] Nuevo server socket thread iniciado desde " + ip + ":" + str(port))
        #self.conn.send(str.encode('Bienvenido '+ ip + ' procesando comando...' + '\n'))  # lo quite por errores en el json


    def liberaComandoMovLock(self):
        if self.comando_mov_lock_adquirido:
            self.comando_mov_lock_adquirido = False
            COMANDO_MOV_LOCK.release()


    def run(self):
        try:
            self._run()
        finally:
            self.liberaComandoMovLock()


    def _run(self):
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
            if comando in COMANDOS_MOVIMIENTO:
                if not COMANDO_MOV_LOCK.acquire(False):
                    print ("[+] ERROR: RUCA OCUPADA")
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- RUCA OCUPADA -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                self.comando_mov_lock_adquirido = True

            # Comandos
            if comando == 'REDUCTOR':           #EJEMPLO: echo REDUCTOR 1 | nc ip 6666  (del 1 al 3)
                if variables.FIRST_INIT_REDUCTOR != 1 or variables.RUEDA_STOP == 1:
                    print ("[+] ERROR: MECANISMO DE REDUCTORES NO INICIALIZADA")
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- MECANISMO DE REDUCTORES NO INICIALIZADO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                variables.REDUCTOR_SET = int(datasplit[1])
                #1 AZUL , 2 ROJO, 3 FUERA
                if variables.REDUCTOR_SET == 1:       #1 AZUL
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.HIGH)
                    time.sleep(1.0)

                    while variables.REDUCTOR_AZUL != 1:     #switch normalmente abierto, mover el motor hasta activar el bit accionando el switch n.o.
                        REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
                        variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS + 10
                        variables.REDUCTOR_FUERA = 0
                        try:
                            self.conn.send(str.encode('+' + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        if time.time() >= self.reductimeout:
                            print ("[+] REDUCTOR: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print ("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break

                elif variables.REDUCTOR_SET == 2:     #2 ROJO
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.HIGH)
                    time.sleep(1.0)

                    while variables.REDUCTOR_ROJO != 1:     #switch normalmente abierto, mover el motor hasta activar el bit accionando el switch n.o.
                        REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS - 10
                        variables.REDUCTOR_FUERA = 0
                        try:
                            self.conn.send(str.encode('-' + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        if time.time() >= self.reductimeout:
                            print ("[+] REDUCTOR: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print ("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break

                elif variables.REDUCTOR_SET == 3:     #3 FUERA - llega en 7000 pasos al centro desde los extremos
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.HIGH)
                    time.sleep(1.0)
                    if variables.REDUCTOR_FUERA != 1:

                        if variables.REDUCTOR_AZUL:
                            for i in range(0, 700):
                                REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                                variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS - 10
                                variables.REDUCTOR_FUERA = 1
                                variables.REDUCTOR_INDICE = 3
                                try:
                                    self.conn.send(str.encode('-' + '\n'))  # echo
                                except BrokenPipeError as e:
                                    pass
                                if time.time() >= self.reductimeout:
                                    print ("[+] REDUCTOR: TIMEOUT")
                                    self.completado = 0
                                    break
                                if variables.RUEDA_STOP == 1:
                                    print ("[+] PARO DE EMERGENCIA")
                                    self.completado = 0
                                    break

                        elif variables.REDUCTOR_ROJO:
                            for i in range(0, 700):
                                REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                                variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS + 10
                                variables.REDUCTOR_FUERA = 1
                                variables.REDUCTOR_INDICE = 3
                                try:
                                    self.conn.send(str.encode('+' + '\n'))  # echo
                                except BrokenPipeError as e:
                                    pass
                                if time.time() >= self.reductimeout:
                                    print ("[+] REDUCTOR: TIMEOUT")
                                    self.completado = 0
                                    break
                                if variables.RUEDA_STOP == 1:
                                    print ("[+] PARO DE EMERGENCIA")
                                    self.completado = 0
                                    break

                        else:
                            while variables.REDUCTOR_ROJO != 1:      #switch normalmente abierto, mover el motor hasta activar el bit accionando el switch n.o.
                                REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                                variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS - 10
                                try:
                                    self.conn.send(str.encode('-' + '\n'))  # echo
                                except BrokenPipeError as e:
                                    pass
                                if time.time() >= self.reductimeout:
                                    print ("[+] REDUCTOR: TIMEOUT")
                                    self.completado = 0
                                    break
                                if variables.RUEDA_STOP == 1:
                                    print ("[+] PARO DE EMERGENCIA")
                                    self.completado = 0
                                    break

                            time.sleep(0.2)
                            for i in range(0, 700):
                                REDUCTOR_MOTOR.step(10, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                                variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS + 10
                                variables.REDUCTOR_FUERA = 1
                                variables.REDUCTOR_INDICE = 3
                                try:
                                    self.conn.send(str.encode('+' + '\n'))  # echo
                                except BrokenPipeError as e:
                                    pass
                                if time.time() >= self.reductimeout:
                                    print ("[+] REDUCTOR: TIMEOUT")
                                    self.completado = 0
                                    break
                                if variables.RUEDA_STOP == 1:
                                    print ("[+] PARO DE EMERGENCIA")
                                    self.completado = 0
                                    break

                else:
                    turnOffReductor()
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break

                turnOffReductor()
                time.sleep(1.0)
                GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
                if self.completado == 1:
                    try:
                        self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print ("[+] OK")
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- VERIFICAR SWITCH LIMITE -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print ("[+] ERROR: VERIFICAR SWITCH LIMITE")
                    variables.FIRST_INIT_REDUCTOR = 0
                self.conn.close()
                break


            elif comando == 'RUEDA':           #EJEMPLO: echo RUEDA 1 | nc ip 6666  (del 1 al 8)
                if variables.FIRST_INIT_RUEDA != 1 or variables.RUEDA_STOP == 1:
                    print ("[+] ERROR: RUEDA DE FILTROS NO INICIALIZADA")
                    variables.RUEDA_ESTADO = "ERROR: RUEDA NO INICIALIZADA"
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- RUEDA DE FILTROS NO INICIALIZADA -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                variables.RUEDA_INDICE_SET = int(datasplit[1])
                if variables.RUEDA_INDICE_SET >= 1 and variables.RUEDA_INDICE_SET <= 8:
                    if variables.RUEDA_INDICE_SET == variables.RUEDA_INDICE:
                        variables.RUEDA_ESTADO = "LISTO"
                        try:
                            self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] OK")
                        self.conn.close()
                        break
                    variables.RUEDA_ESTADO = "MOVIENDO"
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
                    time.sleep(1.0)
                    print ("[+] RUEDA: FRENO OFF")
                    if variables.RUEDA_FRENO_SENSOR == 1:   # Se agrego protección por el nuevo sistema de freno mecánico
                        turnOffRueda()
                        GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                        print ("[+] ERROR: FRENO NO SE DESACTIVO -- RUEDA: FRENO ON")
                        variables.RUEDA_ESTADO = "ERROR: FRENO NO ABRIO"
                        try:
                            self.conn.send(str.encode('ERROR: ' + '-- FRENO NO SE DESACTIVO -- ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        self.conn.close()
                        break
                    variables.RUEDA_SENTIDO = 1      #suma contador, ver interrupciones
                    while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                        RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
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
                    '''
                    time.sleep(1.0)

                    while self.pasosextra < 15 and self.completado != 0:
                        self.pasosextra += 1
                        time.sleep(1.0)
                        if variables.RUEDA_FRENO_SENSOR == 0:
                            GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
                            #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                            time.sleep(1.0)
                            RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                            GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                            #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                            #try:
                                #self.conn.send(str.encode('+' + '\n'))  # echo
                            #except BrokenPipeError as e:
                                #pass
                            print ("[+] RUEDA: PASO EXTRA")
                            self.completado = -1
                        elif variables.RUEDA_FRENO_SENSOR == 1:
                            turnOffRueda()
                            print ("[+] RUEDA: FRENO LLEGO")
                            self.completado = 1
                            break
                        if time.time() >= self.ruedatimeout:
                            print ("[+] RUEDA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print ("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    '''
                    turnOffRueda()
                    time.sleep(0.50)
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                    print ("[+] RUEDA: FRENO ON")
                    if self.completado == 1:
                        variables.RUEDA_ESTADO = "LISTO"
                        try:
                            self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] OK")
                    elif self.completado == 0:
                        variables.RUEDA_ESTADO = "ERROR: NO LLEGO FILTRO - VERIFICAR SWITCH"
                        try:
                            self.conn.send(str.encode('ERROR: ' + '-- VERIFICAR SWITCH LIMITE -- ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] ERROR: VERIFICAR SWITCH LIMITE")
                        variables.FIRST_INIT_RUEDA = 0
                    elif self.completado == -1:
                        variables.RUEDA_ESTADO = "ERROR: FRENO NO ENTRO"
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


            elif comando == 'POLARIZA':           #EJEMPLO: echo POLARIZA 1 | nc ip 6666  (del 1 al 5)
                if variables.FIRST_INIT_POLARIZA != 1 or variables.RUEDA_STOP == 1:
                    print ("[+] RUEDA DE POLARIZADORES NO INICIALIZADA")
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- RUEDA DE POLARIZADORES NO INICIALIZADA -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break
                variables.POLARIZA_INDICE_SET = int(datasplit[1])
                if variables.POLARIZA_INDICE_SET >= 1 and variables.POLARIZA_INDICE_SET <= 5:
                    polariza_pos = variables.POLARIZA_INDICE
                    if polariza_pos == 5:
                        polariza_pos = 0
                    polariza_dif = polariza_pos - variables.POLARIZA_INDICE_SET
                    if polariza_dif == -2 or polariza_dif == -1 or polariza_dif == 3 or polariza_dif == 4:
                        GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
                        #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                        time.sleep(1.0)
                        print ("[+] POLARIZA: FRENO OFF")
                        #time.sleep(1.0)
                        if variables.POLARIZA_FRENO_SENSOR == 1:   # Se agrego protección por el nuevo sistema de freno mecánico
                            turnOffPolariza()
                            GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                            #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                            print ("[+] ERROR: FRENO NO SE DESACTIVO -- POLARIZA: FRENO ON")
                            try:
                                self.conn.send(str.encode('ERROR: ' + '-- FRENO NO SE DESACTIVO -- ' + data + '\n'))  # echo
                            except BrokenPipeError as e:
                                pass
                            self.conn.close()
                            break
                        variables.POLARIZA_SENTIDO = 1      #suma contador, ver interrupciones
                        while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                            POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                            try:
                                self.conn.send(str.encode('+' + '\n'))  # echo
                            except BrokenPipeError as e:
                                pass
                            if time.time() >= self.polarizatimeout:
                                print ("[+] POLARIZA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                        turnOffPolariza()      # Busca posicion de freno correcta
                        time.sleep(0.50)
                        GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                        #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                        time.sleep(1.0)
                        while self.pasosextra < 15 and self.completado != 0:
                            self.pasosextra += 1
                            time.sleep(1.0)
                            if variables.POLARIZA_FRENO_SENSOR == 0:
                                GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
                                #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                                time.sleep(1.0)
                                POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                                variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                                GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                                #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                                try:
                                    self.conn.send(str.encode('+' + '\n'))  # echo
                                except BrokenPipeError as e:
                                    pass
                                print ("[+] POLARIZA: PASO EXTRA")
                                self.completado = -1
                            elif variables.POLARIZA_FRENO_SENSOR == 1:
                                turnOffPolariza()
                                print ("[+] POLARIZA: FRENO LLEGO")
                                self.completado = 1
                                break
                            if time.time() >= self.polarizatimeout:
                                print ("[+] POLARIZA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                    elif polariza_dif != 0 and polariza_dif != -5:
                        GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
                        #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                        time.sleep(1.0)
                        print ("[+] POLARIZA: FRENO OFF")
                        if variables.POLARIZA_FRENO_SENSOR == 1:   # Se agrego protección por el nuevo sistema de freno mecánico
                            turnOffPolariza()
                            GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                            #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                            print ("[+] ERROR: FRENO NO SE DESACTIVO -- POLARIZA: FRENO ON")
                            try:
                                self.conn.send(str.encode('ERROR: ' + '-- FRENO NO SE DESACTIVO -- ' + data + '\n'))  # echo
                            except BrokenPipeError as e:
                                pass
                            self.conn.close()
                            break
                        variables.POLARIZA_SENTIDO = 0      #resta contador, ver interrupciones
                        while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                            POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.POLARIZA_PASOS = variables.POLARIZA_PASOS - 1
                            try:
                                self.conn.send(str.encode('-' + '\n'))  # echo
                            except BrokenPipeError as e:
                                pass
                            if time.time() >= self.polarizatimeout:
                                print ("[+] POLARIZA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                        time.sleep(1.0)
                        POLARIZA_MOTOR.step(80, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS - 80
                        variables.POLARIZA_INDICE = variables.POLARIZA_INDICE - 1     #resta un contador para regresar en un mismo sentido siempre
                        print (">>Restado 1 en POLARIZA_INDICE_PIN para Compensar>>")
                        print ("POLARIZA_INDICE = " + str(variables.POLARIZA_INDICE))
                        variables.POLARIZA_SENTIDO = 1      #suma contador, ver interrupciones
                        time.sleep(1.0)
                        while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                            POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                            variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                            try:
                                self.conn.send(str.encode('+' + '\n'))  # echo
                            except BrokenPipeError as e:
                                pass
                            if time.time() >= self.polarizatimeout:
                                print ("[+] POLARIZA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break
                        turnOffPolariza()      # Busca posicion de freno correcta
                        time.sleep(0.50)
                        GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                        #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                        time.sleep(1.0)
                        while self.pasosextra < 15 and self.completado != 0:
                            self.pasosextra += 1
                            time.sleep(1.0)
                            if variables.POLARIZA_FRENO_SENSOR == 0:
                                GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
                                #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                                time.sleep(1.0)
                                POLARIZA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                                variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                                GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                                #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                                try:
                                    self.conn.send(str.encode('+' + '\n'))  # echo
                                except BrokenPipeError as e:
                                    pass
                                print ("[+] POLARIZA: PASO EXTRA")
                                self.completado = -1
                            elif variables.POLARIZA_FRENO_SENSOR == 1:
                                turnOffPolariza()
                                print ("[+] POLARIZA: FRENO LLEGO")
                                self.completado = 1
                                break
                            if time.time() >= self.polarizatimeout:
                                print ("[+] POLARIZA: TIMEOUT")
                                self.completado = 0
                                break
                            if variables.RUEDA_STOP == 1:
                                print ("[+] PARO DE EMERGENCIA")
                                self.completado = 0
                                break

                    turnOffPolariza()
                    time.sleep(1.0)
                    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                    print ("[+] POLARIZA: FRENO ON")
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
                        variables.FIRST_INIT_POLARIZA = 0
                    elif self.completado == -1:
                        try:
                            self.conn.send(str.encode('ERROR: ' + '-- FRENO POLARIZA NO LLEGO A SU POSICION -- ' + data + '\n'))  # echo
                        except BrokenPipeError as e:
                            pass
                        print ("[+] ERROR: FRENO POLARIZA NO LLEGO A SU POSICION")
                        variables.FIRST_INIT_POLARIZA = 0
                    self.conn.close()
                    break
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break


            elif comando == 'MUEVE':        #EJEMPLO: echo MUEVE MOTOR(1-2-3) #STEPS DIR(1/0) | nc ip 6666
                motor = int(datasplit[1])
                pasos = int(datasplit[2])
                sentido = int(datasplit[3])

                if sentido == 1:
                    direccion = Adafruit_MotorHAT.FORWARD
                elif sentido == 0:
                    direccion = Adafruit_MotorHAT.BACKWARD
                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break

                if motor == 1:
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.HIGH)
                    #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    time.sleep(1.0)
                    RUEDA_MOTOR.step(pasos, direccion, Adafruit_MotorHAT.DOUBLE)
                    if sentido == 1:
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + pasos
                    else:
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS - pasos
                    turnOffRueda()
                    time.sleep(1.0)
                    GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                    #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(0)

                elif motor == 2:
                    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.HIGH)
                    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(100)
                    time.sleep(1.0)
                    POLARIZA_MOTOR.step(pasos, direccion, Adafruit_MotorHAT.DOUBLE)
                    if sentido == 1:
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + pasos
                    else:
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS - pasos
                    turnOffPolariza()
                    time.sleep(1.0)
                    GPIO.output(POLARIZA_FRENO_OUT_PIN, GPIO.LOW)
                    #POLARIZA_FRENO_OUT_PWM.ChangeDutyCycle(0)

                elif motor == 3:
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.HIGH)
                    time.sleep(1.0)
                    REDUCTOR_MOTOR.step(pasos, direccion, Adafruit_MotorHAT.DOUBLE)
                    if sentido == 1:
                        variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS + pasos
                    else:
                        variables.REDUCTOR_PASOS = variables.REDUCTOR_PASOS - pasos
                    turnOffReductor()
                    time.sleep(1.0)
                    GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)

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
                variables.RUEDA_ESTADO = "ERROR: PARO DE EMERGENCIA"
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
                variables.RUEDA_ESTADO = "Iniciando RUCA"
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
                variables.RUEDA_SWITCH = GPIO.input(RUEDA_INDICE_PIN)
                variables.RUEDA_INICIO = GPIO.input(RUEDA_INICIO_PIN)
                variables.B_START = GPIO.input(B_START_PIN)
                variables.B_STOP = GPIO.input(B_STOP_PIN)
                variables.B_UP = GPIO.input(B_UP_PIN)
                variables.B_DOWN = GPIO.input(B_DOWN_PIN)

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
                    'RUEDA_PARO_EMERGENCIA': variables.RUEDA_STOP,
                    'RUEDA_SWITCH': variables.RUEDA_SWITCH,
                    'RUEDA_ESTADO': variables.RUEDA_ESTADO,
                    'RUEDA_SPEED': variables.RUEDA_SPEED,
                    'B_START': variables.B_START,
                    'B_STOP': variables.B_STOP,
                    'B_UP': variables.B_UP,
                    'B_DOWN': variables.B_DOWN
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


            elif comando == 'CAMBIO':  # CAMBIA Nombres de Filtros
                print("Petición del Cliente por Cambio de Nombres: ", data)
                nombresjson = data[6:]
                nombresjson2 = json.loads(nombresjson)

                # Ruta del archivo JSON
                ruta_json = '/home/pi/Documents/Ruca/filtros.json'

                # 1. Cargar el archivo existente si existe
                datos_actuales = {}
                if os.path.isfile(ruta_json):
                    try:
                        with open(ruta_json, 'r') as infile:
                            datos_actuales = json.load(infile)
                    except Exception as e:
                        print("[*] ERROR al leer filtros.json:", e)
                        pass

                # 2. Actualizar solo las claves recibidas
                datos_actuales.update(nombresjson2)

                # 3. Guardar el archivo actualizado
                try:
                    with open(ruta_json, 'w') as outfile:
                        json.dump(datos_actuales, outfile, indent=4)
                    print("[+] filtros.json actualizado correctamente con las nuevas claves.")
                except Exception as e:
                    print("[*] ERROR al guardar filtros.json:", e)
                    pass

                # 4. Aplicar cambios en variables si están presentes
                for clave, valor in nombresjson2.items():
                    if clave == 'FILTRO01':
                        variables.N_FILTRO_01 = valor
                    elif clave == 'FILTRO02':
                        variables.N_FILTRO_02 = valor
                    elif clave == 'FILTRO03':
                        variables.N_FILTRO_03 = valor
                    elif clave == 'FILTRO04':
                        variables.N_FILTRO_04 = valor
                    elif clave == 'FILTRO05':
                        variables.N_FILTRO_05 = valor
                    elif clave == 'FILTRO06':
                        variables.N_FILTRO_06 = valor
                    elif clave == 'FILTRO07':
                        variables.N_FILTRO_07 = valor
                    elif clave == 'FILTRO08':
                        variables.N_FILTRO_08 = valor
                    elif clave == 'POLARIZA01':
                        variables.N_POLARIZA_01 = valor
                    elif clave == 'POLARIZA02':
                        variables.N_POLARIZA_02 = valor
                    elif clave == 'POLARIZA03':
                        variables.N_POLARIZA_03 = valor
                    elif clave == 'POLARIZA04':
                        variables.N_POLARIZA_04 = valor
                    elif clave == 'POLARIZA05':
                        variables.N_POLARIZA_05 = valor
                    elif clave == 'REDUCTOR01':
                        variables.N_REDUCTOR_01 = valor
                    elif clave == 'REDUCTOR02':
                        variables.N_REDUCTOR_02 = valor
                    elif clave == 'REDUCTOR03':
                        variables.N_REDUCTOR_03 = valor

                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'SPEED':
                speed = int(datasplit[1])
                if speed <= 0 or speed > 200:
                    speed = 80
                elif speed > 0 and speed <=200:
                    speed = speed
                else:
                    speed = 80

                variables.RUEDA_SPEED = speed
                RUEDA_MOTOR.setSpeed(speed)
                print ("[+] RUEDA_SPEED CAMBIO A: " + str(variables.RUEDA_SPEED))

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



def cargar_filtros_desde_json():
    try:
        with open('/home/pi/Documents/Ruca/filtros.json') as jsonfile:
            nombresjson2 = json.load(jsonfile)
            print("[+] Filtros y configuraciones cargadas correctamente")
            print("[*] Contenido del JSON cargado:\n",
                  json.dumps(nombresjson2, indent=4))  # Imprime bonito

            if 'FILTRO01' in nombresjson2:
                variables.N_FILTRO_01 = nombresjson2['FILTRO01']
            if 'FILTRO02' in nombresjson2:
                variables.N_FILTRO_02 = nombresjson2['FILTRO02']
            if 'FILTRO03' in nombresjson2:
                variables.N_FILTRO_03 = nombresjson2['FILTRO03']
            if 'FILTRO04' in nombresjson2:
                variables.N_FILTRO_04 = nombresjson2['FILTRO04']
            if 'FILTRO05' in nombresjson2:
                variables.N_FILTRO_05 = nombresjson2['FILTRO05']
            if 'FILTRO06' in nombresjson2:
                variables.N_FILTRO_06 = nombresjson2['FILTRO06']
            if 'FILTRO07' in nombresjson2:
                variables.N_FILTRO_07 = nombresjson2['FILTRO07']
            if 'FILTRO08' in nombresjson2:
                variables.N_FILTRO_08 = nombresjson2['FILTRO08']

            if 'POLARIZA01' in nombresjson2:
                variables.N_POLARIZA_01 = nombresjson2['POLARIZA01']
            if 'POLARIZA02' in nombresjson2:
                variables.N_POLARIZA_02 = nombresjson2['POLARIZA02']
            if 'POLARIZA03' in nombresjson2:
                variables.N_POLARIZA_03 = nombresjson2['POLARIZA03']
            if 'POLARIZA04' in nombresjson2:
                variables.N_POLARIZA_04 = nombresjson2['POLARIZA04']
            if 'POLARIZA05' in nombresjson2:
                variables.N_POLARIZA_05 = nombresjson2['POLARIZA05']

            if 'REDUCTOR01' in nombresjson2:
                variables.N_REDUCTOR_01 = nombresjson2['REDUCTOR01']
            if 'REDUCTOR02' in nombresjson2:
                variables.N_REDUCTOR_02 = nombresjson2['REDUCTOR02']
            if 'REDUCTOR03' in nombresjson2:
                variables.N_REDUCTOR_03 = nombresjson2['REDUCTOR03']

    except Exception as e:
        print("[*] ERROR - No se pudo cargar filtros.json - Omitiendo")
        print("Detalle:", str(e))
        pass



# Programa Principal
try:
    turnOffMotors()
    variables = Ruca2_variables.Rueda()      #Variables
    principal = Principal()
    principal.run()

    print ("[+] SERVIDOR DE LA RUCA 2.0 - RUEDA DE FILTROS Iniciado! Presione CTRL+C para Salir")
    # become a server socket
    tcpServer.listen(12)

    cargar_filtros_desde_json()

    while True:
        print("Esperando por Conexiones en el puerto: " + str(TCP_PORT))
        (conn, (ip, port)) = tcpServer.accept()

        threadSockets = ClientThread(ip, port, conn)
        threadSockets.daemon = True   # opcional, para que no bloqueen al salir
        threadSockets.start()
        
    """
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
    """

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
    tcpServer.shutdown(socket.SHUT_RDWR)
    tcpServer.close()
