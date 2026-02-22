#!/usr/bin/env python3

'''
RUCA 2.0 - RUEDA DE FILTROS RAMPA TEST
Version 1.0-dev          11/Noviembre/2024
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
POLA_INICIO_PIN = 27
POLARIZA_INDICE_PIN = 22
REDUCTOR_AZUL_PIN = 5
REDUCTOR_ROJO_PIN = 6
RUEDA_FRENO_IN_PIN = 18
POLA_FRENO_IN_PIN = 24

# GPIOS Salidas
RUEDA_FRENO_OUT_PIN = 23
POLA_FRENO_OUT_PIN = 12
REDUCTOR_FRENO_OUT_PIN = 16



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
POLA_MOTOR = bottomhat.getStepper(200, 2)      # 200 steps/rev, motor port #2
# REDUCTOR_MOTOR = tophat.getStepper(200, 1)      # 200 steps/rev, motor port #1

RUEDA_MOTOR.setSpeed(80)          # 60 RPM
POLA_MOTOR.setSpeed(80)          # 60 RPM
# REDUCTOR_MOTOR.setSpeed(200)          # 200 RPM

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def turnOffRueda():
    bottomhat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)


def turnOffPola():
    bottomhat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottomhat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)


# recommended for auto-disabling motors on shutdown!
atexit.register(turnOffMotors)



# Envia a posiciones de inicio al ARRANCAR la rueda de filtros y rueda de polarizadores
def FirstinitPos():
    variables.FIRST_INIT_RUEDA = 1
    variables.FIRST_INIT_POLA = 1
    time.sleep(1.0)


# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread):
    def __init__(self,ip,port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.ruedatimeout = time.time() + 20*1.00   # 1 minuto desde el inicio
        self.polatimeout = time.time() + 20*1.00   # 1 minuto desde el inicio
        self.completado = 1
        self.pasosextra = 0
        print ("[+] Nuevo server socket thread iniciado desde " + ip + ":" + str(port))
        #self.conn.send(str.encode('Bienvenido '+ ip + ' procesando comando...' + '\n'))  # lo quite por errores en el json


    def run(self):
        #RUEDA_MOTOR bottomhat 1
        #POLA_MOTOR bottomhat 2
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
                variables.RUEDA_INDICE_SET = int(datasplit[1])
                if variables.RUEDA_INDICE_SET == 1:
                    time.sleep(1.0)
                    variables.RUEDA_SENTIDO = 1      #suma contador, ver interrupciones
                    # pruebas de la rampa
                    # RUEDA_MOTOR.setSpeed(80)
                    RUEDA_MOTOR.setSpeed(1)
                    for i in range(1, 201, 1):
                        if i > 80:
                            i = 80
                        RUEDA_MOTOR.setSpeed(i)
                        print(i)
                        RUEDA_MOTOR.step(1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
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
                    # pruebas de la rampa
                    turnOffRueda()      
                    self.completado = 1

                elif variables.RUEDA_INDICE_SET == 2:
                    time.sleep(1.0)
                    print ("[+] RUEDA: FRENO OFF")
                    variables.RUEDA_SENTIDO = 0      #resta contador, ver interrupciones
                    # pruebas de la rampa
                    # RUEDA_MOTOR.setSpeed(80)
                    RUEDA_MOTOR.setSpeed(1)
                    for i in range(1, 201, 1):
                        if i > 80:
                            i = 80
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
                    # pruebas de la rampa
                    time.sleep(0.50)
                    print ("PASANDOSE PARA LLEGAR EN MISMO SENTIDO")
                    RUEDA_MOTOR.step(80, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                    variables.RUEDA_PASOS = variables.RUEDA_PASOS - 80
                    variables.RUEDA_INDICE = variables.RUEDA_INDICE - 1     #resta un contador para regresar en un mismo sentido siempre
                    print (">>Restado 1 en RUEDA_INDICE_PIN para Compensar>>")
                    print ("RUEDA_INDICE = " + str(variables.RUEDA_INDICE))
                    variables.RUEDA_SENTIDO = 1      #suma contador, ver interrupciones
                    time.sleep(0.50)
                    print ("REGRESANDO PARA LLEGAR EN MISMO SENTIDO")
                    RUEDA_MOTOR.step(80, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                    variables.RUEDA_PASOS = variables.RUEDA_PASOS + 80
                    turnOffRueda()      # Busca posicion de freno correcta
                    self.completado = 1

                elif variables.RUEDA_INDICE_SET == 3:
                    time.sleep(1.0)
                    variables.RUEDA_SENTIDO = 1  # suma contador, ver interrupciones
                    RUEDA_MOTOR.setSpeed(80)
                    while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                        RUEDA_MOTOR.step(
                            1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                        if time.time() >= self.ruedatimeout:
                            print("[+] RUEDA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffRueda()
                    self.completado = 1
                
                elif variables.RUEDA_INDICE_SET == 4:
                    time.sleep(1.0)
                    variables.RUEDA_SENTIDO = 1  # suma contador, ver interrupciones
                    RUEDA_MOTOR.setSpeed(80)
                    while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                        RUEDA_MOTOR.step(
                            1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                        if time.time() >= self.ruedatimeout:
                            print("[+] RUEDA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffRueda()
                    self.completado = 1

                elif variables.RUEDA_INDICE_SET == 5:
                    time.sleep(1.0)
                    variables.RUEDA_SENTIDO = 1  # suma contador, ver interrupciones
                    RUEDA_MOTOR.setSpeed(80)
                    while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                        RUEDA_MOTOR.step(
                            200, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                        if time.time() >= self.ruedatimeout:
                            print("[+] RUEDA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffRueda()
                    self.completado = 1

                elif variables.RUEDA_INDICE_SET == 6:
                    time.sleep(1.0)
                    variables.RUEDA_SENTIDO = 1  # suma contador, ver interrupciones
                    RUEDA_MOTOR.setSpeed(80)
                    while variables.RUEDA_INDICE != variables.RUEDA_INDICE_SET:
                        RUEDA_MOTOR.step(
                            200, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                        variables.RUEDA_PASOS = variables.RUEDA_PASOS + 1
                        if time.time() >= self.ruedatimeout:
                            print("[+] RUEDA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffRueda()
                    self.completado = 1

                else:
                    try:
                        self.conn.send(str.encode('ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break

                turnOffRueda()      # Busca posicion de freno correcta
                self.completado = 1
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
                    variables.FIRST_INIT_RUEDA = 0
                self.conn.close()
                break



            # EJEMPLO: echo POLA 1 | nc ip 6666  (del 1 al 8)
            elif comando == 'POLA':
                variables.POLARIZA_INDICE_SET = int(datasplit[1])
                if variables.POLARIZA_INDICE_SET == 1:
                    time.sleep(1.0)
                    variables.POLA_SENTIDO = 1  # suma contador, ver interrupciones
                    # pruebas de la rampa
                    # POLA_MOTOR.setSpeed(80)
                    POLA_MOTOR.setSpeed(1)
                    for i in range(1, 201, 1):
                        if i > 80:
                            i = 80
                        POLA_MOTOR.setSpeed(i)
                        print(i)
                        POLA_MOTOR.step(
                            1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                    while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                        POLA_MOTOR.step(
                            1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                        if time.time() >= self.polatimeout:
                            print("[+] POLA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    # pruebas de la rampa
                    turnOffRueda()
                    self.completado = 1

                elif variables.POLARIZA_INDICE_SET == 2:
                    time.sleep(1.0)
                    print("[+] POLA: FRENO OFF")
                    variables.POLA_SENTIDO = 0  # resta contador, ver interrupciones
                    # pruebas de la rampa
                    # POLA_MOTOR.setSpeed(80)
                    POLA_MOTOR.setSpeed(1)
                    for i in range(1, 201, 1):
                        if i > 80:
                            i = 80
                        POLA_MOTOR.setSpeed(i)
                        print(i)
                        POLA_MOTOR.step(
                            1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS - 1
                    while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                        POLA_MOTOR.step(
                            1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS - 1
                        # try:
                        # self.conn.send(str.encode('+' + '\n'))  # echo
                        # except BrokenPipeError as e:
                        # pass
                        if time.time() >= self.polatimeout:
                            print("[+] POLA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    # pruebas de la rampa
                    time.sleep(0.50)
                    print("PASANDOSE PARA LLEGAR EN MISMO SENTIDO")
                    POLA_MOTOR.step(
                        80, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.MICROSTEP)
                    variables.POLARIZA_PASOS = variables.POLARIZA_PASOS - 80
                    # resta un contador para regresar en un mismo sentido siempre
                    variables.POLARIZA_INDICE = variables.POLARIZA_INDICE - 1
                    print(">>Restado 1 en POLARIZA_INDICE_PIN para Compensar>>")
                    print("POLARIZA_INDICE = " + str(variables.POLARIZA_INDICE))
                    variables.POLA_SENTIDO = 1  # suma contador, ver interrupciones
                    time.sleep(0.50)
                    print("REGRESANDO PARA LLEGAR EN MISMO SENTIDO")
                    POLA_MOTOR.step(
                        80, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
                    variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 80
                    turnOffPola()      # Busca posicion de freno correcta
                    self.completado = 1

                elif variables.POLARIZA_INDICE_SET == 3:
                    time.sleep(1.0)
                    variables.POLA_SENTIDO = 1  # suma contador, ver interrupciones
                    POLA_MOTOR.setSpeed(80)
                    while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                        POLA_MOTOR.step(
                            1, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                        if time.time() >= self.polatimeout:
                            print("[+] POLA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffPola()
                    self.completado = 1

                elif variables.POLARIZA_INDICE_SET == 4:
                    time.sleep(1.0)
                    variables.POLA_SENTIDO = 1  # suma contador, ver interrupciones
                    POLA_MOTOR.setSpeed(80)
                    while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                        POLA_MOTOR.step(
                            1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                        if time.time() >= self.polatimeout:
                            print("[+] POLA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffPola()
                    self.completado = 1

                elif variables.POLARIZA_INDICE_SET == 5:
                    time.sleep(1.0)
                    variables.POLA_SENTIDO = 1  # suma contador, ver interrupciones
                    POLA_MOTOR.setSpeed(80)
                    while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                        POLA_MOTOR.step(
                            200, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                        if time.time() >= self.polatimeout:
                            print("[+] POLA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffPola()
                    self.completado = 1

                elif variables.POLARIZA_INDICE_SET == 6:
                    time.sleep(1.0)
                    variables.POLA_SENTIDO = 1  # suma contador, ver interrupciones
                    POLA_MOTOR.setSpeed(80)
                    while variables.POLARIZA_INDICE != variables.POLARIZA_INDICE_SET:
                        POLA_MOTOR.step(
                            200, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.MICROSTEP)
                        variables.POLARIZA_PASOS = variables.POLARIZA_PASOS + 1
                        if time.time() >= self.polatimeout:
                            print("[+] POLA: TIMEOUT")
                            self.completado = 0
                            break
                        if variables.RUEDA_STOP == 1:
                            print("[+] PARO DE EMERGENCIA")
                            self.completado = 0
                            break
                    turnOffPola()
                    self.completado = 1

                else:
                    try:
                        self.conn.send(str.encode(
                            'ERROR: ' + '-- COMANDO ERRONEO -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    self.conn.close()
                    break

                turnOffPola()      # Busca posicion de freno correcta
                self.completado = 1
                if self.completado == 1:
                    try:
                        self.conn.send(str.encode(
                            'OK: ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print("[+] OK")
                else:
                    try:
                        self.conn.send(str.encode(
                            'ERROR: ' + '-- VERIFICAR SWITCH LIMITE -- ' + data + '\n'))  # echo
                    except BrokenPipeError as e:
                        pass
                    print("[+] ERROR: VERIFICAR SWITCH LIMITE")
                    variables.FIRST_INIT_POLA = 0
                self.conn.close()
                break




            #Emergency Stop
            elif comando == 'STOP':
                variables.RUEDA_STOP = 1
                variables.FIRST_INIT_RUEDA = 0
                variables.FIRST_INIT_POLA = 0
                variables.FIRST_INIT_REDUCTOR = 0
                turnOffMotors()
                time.sleep(1.0)
                GPIO.output(RUEDA_FRENO_OUT_PIN, GPIO.LOW)
                #RUEDA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                GPIO.output(POLA_FRENO_OUT_PIN, GPIO.LOW)
                #POLA_FRENO_OUT_PWM.ChangeDutyCycle(0)
                GPIO.output(REDUCTOR_FRENO_OUT_PIN, GPIO.LOW)
                print ("[+] PARO DE EMERGENCIA")
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
    GPIO.cleanup()
    print ("Adios Viajero")
    sys.exit()
    #session.close()
    #session.dispose()
    tcpServer.shutdown()
    tcpServer.close()
