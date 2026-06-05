#!/usr/bin/env python3

'''
RUCA 2.0 - CLASE GLOBAL DE LAS VARIABLES
Version 0.4-dev          26/Julio/2024
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

Rueda de filtros RUCA 2.0, consiste en una rueda de filtros, un polarizador,
dos reductores focales y una platina giratoria.
Funciones Añadidas:

Ver. 0.4 - Speed y Switch Rueda
Ver. 0.3 - Paro de emergencia
Ver. 0.2 - Nombres de Filtros
Ver. 0.1 - Implementada
'''



#RUEDA DE FILTROS
class Rueda():
    def __init__(self):
        #print ("[+] Variables de la Rueda de Filtros Cargadas")
        # Entradas
        self.RUEDA_INICIO = 0
        self.RUEDA_INDICE = 0
        self.POLARIZA_INICIO = 0
        self.POLARIZA_INDICE = 0
        self.REDUCTOR_AZUL = 0
        self.REDUCTOR_ROJO = 0
        self.REDUCTOR_FUERA = 0
        self.REDUCTOR_INDICE = 0
        self.RUEDA_FRENO_SENSOR = 0
        self.POLARIZA_FRENO_SENSOR = 0
        self.REDUCTOR_FRENO_SENSOR = 0
        self.RUEDA_SWITCH = 0
        self.RUEDA_SPEED = 80
        self.RUEDA_ESTADO = 'ARRANCANDO'

        # Salidas
        self.RUEDA_FRENO = 0
        self.POLARIZA_FRENO = 0
        self.REDUCTOR_FRENO = 0

        # Posición deseadas
        self.RUEDA_INDICE_SET = 0        #1-8
        self.POLARIZA_INDICE_SET = 0     #1-5
        self.REDUCTOR_SET = 0            #1 AZUL , 2 ROJO, 3 FUERA

        # Pasos de Motores
        self.RUEDA_PASOS = 0
        self.POLARIZA_PASOS = 0
        self.REDUCTOR_PASOS = 0

        # Banderas de Inicialización
        self.FIRST_INIT_RUEDA = 0
        self.FIRST_INIT_POLARIZA = 0
        self.FIRST_INIT_REDUCTOR = 0
        self.RUEDA_STOP = 0

        # Sentido de Movimiento
        self.RUEDA_SENTIDO = 1          #1/0 Forward/Backward
        self.POLARIZA_SENTIDO = 1       #1/0 Forward/Backward

        # Nombre de FILTROS
        self.N_FILTRO_01 = 'VACIO'
        self.N_FILTRO_02 = 'ESPACIO 02'
        self.N_FILTRO_03 = 'ESPACIO 03'
        self.N_FILTRO_04 = 'ESPACIO 04'
        self.N_FILTRO_05 = 'ESPACIO 05'
        self.N_FILTRO_06 = 'ESPACIO 06'
        self.N_FILTRO_07 = 'ESPACIO 07'
        self.N_FILTRO_08 = 'ESPACIO 08'

        self.N_POLARIZA_01 = 'VACIO'
        self.N_POLARIZA_02 = '0'
        self.N_POLARIZA_03 = '45'
        self.N_POLARIZA_04 = '90'
        self.N_POLARIZA_05 = '135'

        self.N_REDUCTOR_01 = 'AZUL'
        self.N_REDUCTOR_02 = 'ROJO'
        self.N_REDUCTOR_03 = 'VACIO'



#PLATINA GIRATORIA
class Platina():
    def __init__(self):
        #print ("[+] Variables de la Platina Giratoria Cargadas")
        # Entradas
        self.PLATINA_INICIO = 0
        self.PLATINA_FIN = 0
        self.PLATINA_FRENO_SENSOR = 0

        # Salidas
        self.PLATINA_FRENO = 0

        # Posición de Platina
        self.PLATINA_ENC = 0     #posicion actual encoder
        self.PLATINA_POS = 0     #posicion actual en porcentaje respecto al rango min-max
        self.PLATINA_SET = 0     #posicion deseada encoder o posición (automaticamente se elige)
        self.PLATINA_MIN = 0
        self.PLATINA_MAX = 0         #max encoder counts 4294967295
        self.PLATINA_DEAD_ZONE = 5   #zona muerta

        # Variables extras
        self.TEMP_ROBO_1 = 0
        self.FIRST_INIT_PLATINA = 0
        self.PLATINA_STOP = 0
