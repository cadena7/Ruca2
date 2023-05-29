#!/usr/bin/env python3

'''
RUCA 2.0 - INTERFAZ WEB DE USUARIO
Version 0.5-dev          05/Nov/2019
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


Funciones Añadidas:

Ver. 0.5 - Se agrego bandera de paro de emergencia
Ver. 0.4 - Se deshabilito todo lo relacionado con la platina
Ver. 0.4 - Se añadieron botones para inicializar rueda de filtros y platina
Ver. 0.3 - Se leen las variables pidiendolas por medio de comando de sockets y se añadieron URL's para los comandois
Ver. 0.2 - Importando variables globales del script principal
Ver. 0.1 - En Desarrollo
'''

from flask import Flask, render_template, redirect, request, flash, url_for, session, g, abort, jsonify
import os
import sys
import time, datetime
import subprocess
import simplejson as json


app = Flask(__name__, static_url_path='')
app.secret_key = "\xc8\xc1\xf7:\x8a\x9e\x9d\x17\xb0\xd9\xee\x04tOo\xf3:$\xb5,\xbc\x7fxz"



@app.route("/")
@app.route("/index.html")
def inicio():
    nombres1 = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    nombres2 = nombres1.communicate(str.encode("NOMBRE"))[0]  #regresa un tuple [0,1]
    print ("[+] SOLICITANDO NOMBRES FILTROS")
    print(nombres2)
    nombresjson1 = nombres2.decode('utf-8')    #decodificar el mensaje
    print(nombresjson1)
    nombresjson2 = json.loads(nombresjson1)
    print ("[+] NOMBRES FILTROS OK")
    nombres1.kill()

    Filtro01 = nombresjson2['Filtro01']                              #0
    Filtro02 = nombresjson2['Filtro02']                              #1
    Filtro03 = nombresjson2['Filtro03']                              #2
    Filtro04 = nombresjson2['Filtro04']                              #3
    Filtro05 = nombresjson2['Filtro05']                              #4
    Filtro06 = nombresjson2['Filtro06']                              #5
    Filtro07 = nombresjson2['Filtro07']                              #6
    Filtro08 = nombresjson2['Filtro08']                              #7

    Polarizador01 = nombresjson2['Polariza01']                       #0
    Polarizador02 = nombresjson2['Polariza02']                       #1
    Polarizador03 = nombresjson2['Polariza03']                       #2
    Polarizador04 = nombresjson2['Polariza04']                       #3
    Polarizador05 = nombresjson2['Polariza05']                       #4

    Reductor01 = nombresjson2['Reductor01']                          #0
    Reductor02 = nombresjson2['Reductor02']                          #1
    Reductor03 = nombresjson2['Reductor03']                          #2

    TablaFiltros = [Filtro01, Filtro02, Filtro03, Filtro04, Filtro05, Filtro06, Filtro07, Filtro08]
    TablaPolarizadores = [Polarizador01, Polarizador02, Polarizador03, Polarizador04, Polarizador05]
    TablaReductores = [Reductor01, Reductor02, Reductor03]

    estado1 = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    estado2 = estado1.communicate(str.encode("ESTADO"))[0]  #regresa un tuple [0,1]
    print ("[+] SOLICITANDO VARIABLES ESTADORUEDA")
    print(estado2)
    estadojson1 = estado2.decode('utf-8')    #decodificar el mensaje
    print(estadojson1)
    estadojson2 = json.loads(estadojson1)
    print ("[+] VARIABLES ESTADORUEDA OK")
    estado1.kill()

    RUEDA_INICIO = estadojson2['RUEDA_INICIO']                       #0
    RUEDA_INDICE = estadojson2['RUEDA_INDICE']                       #1
    POLARIZA_INICIO = estadojson2['POLARIZA_INICIO']                 #2
    POLARIZA_INDICE = estadojson2['POLARIZA_INDICE']                 #3
    REDUCTOR_AZUL= estadojson2['REDUCTOR_AZUL']                      #4
    REDUCTOR_ROJO = estadojson2['REDUCTOR_ROJO']                     #5
    REDUCTOR_FUERA = estadojson2['REDUCTOR_FUERA']                   #6
    RUEDA_FRENO = estadojson2['RUEDA_FRENO']                         #7
    POLARIZA_FRENO = estadojson2['POLARIZA_FRENO']                   #8
    REDUCTOR_FRENO = estadojson2['REDUCTOR_FRENO']                   #9
    RUEDA_INDICE_SET = estadojson2['RUEDA_INDICE_SET']               #10
    POLARIZA_INDICE_SET = estadojson2['POLARIZA_INDICE_SET']         #11
    REDUCTOR_SET = estadojson2['REDUCTOR_SET']                       #12
    RUEDA_PASOS = estadojson2['RUEDA_PASOS']                         #13
    POLARIZA_PASOS = estadojson2['POLARIZA_PASOS']                   #14
    REDUCTOR_PASOS = estadojson2['REDUCTOR_PASOS']                   #15
    FIRST_INIT_RUEDA = estadojson2['FIRST_INIT_RUEDA']               #16
    FIRST_INIT_POLARIZA = estadojson2['FIRST_INIT_POLARIZA']         #17
    FIRST_INIT_REDUCTOR = estadojson2['FIRST_INIT_REDUCTOR']         #18
    RUEDA_FRENO_SENSOR = estadojson2['RUEDA_FRENO_SENSOR']           #19
    POLARIZA_FRENO_SENSOR = estadojson2['POLARIZA_FRENO_SENSOR']     #20
    REDUCTOR_INDICE = estadojson2['REDUCTOR_INDICE']                 #21
    RUEDA_PARO_EMERGENCIA = estadojson2['RUEDA_PARO_EMERGENCIA']     #22

    TablaEstadoRueda = [RUEDA_INICIO, RUEDA_INDICE, POLARIZA_INICIO, POLARIZA_INDICE, REDUCTOR_AZUL, REDUCTOR_ROJO, REDUCTOR_FUERA, RUEDA_FRENO, POLARIZA_FRENO,
                        REDUCTOR_FRENO, RUEDA_INDICE_SET, POLARIZA_INDICE_SET, REDUCTOR_SET, RUEDA_PASOS, POLARIZA_PASOS, REDUCTOR_PASOS, FIRST_INIT_RUEDA,
                        FIRST_INIT_POLARIZA, FIRST_INIT_REDUCTOR, RUEDA_FRENO_SENSOR, POLARIZA_FRENO_SENSOR, REDUCTOR_INDICE, RUEDA_PARO_EMERGENCIA]
    '''
    estado2 = subprocess.Popen("nc localhost 7777", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    estado3 = estado2.communicate(str.encode("ESTADO"))[0]  #regresa un tuple [0,1]
    print ("[+] SOLICITANDO VARIABLES ESTADOPLATINA")
    print(estado3)
    estadojson3 = estado3.decode('utf-8')    #decodificar el mensaje
    print(estadojson3)
    estadojson4 = json.loads(estadojson3)
    print ("[+] VARIABLES ESTADOPLATINA OK")
    estado2.kill()

    PLATINA_INICIO = estadojson4['PLATINA_INICIO']                    #0
    PLATINA_FIN = estadojson4['PLATINA_FIN']                          #1
    PLATINA_ENC = estadojson4['PLATINA_ENC']                          #2
    PLATINA_POS = estadojson4['PLATINA_POS']                          #3
    PLATINA_SET= estadojson4['PLATINA_SET']                           #4
    PLATINA_MIN = estadojson4['PLATINA_MIN']                          #5
    PLATINA_MAX = estadojson4['PLATINA_MAX']                          #6
    PLATINA_FRENO = estadojson4['PLATINA_FRENO']                      #7
    TEMP_ROBO_1 = estadojson4['TEMP_ROBO_1']                          #8
    FIRST_INIT_PLATINA = estadojson4['FIRST_INIT_PLATINA']            #9
    PLATINA_FRENO_SENSOR = estadojson4['PLATINA_FRENO_SENSOR']        #10

    PLATINA_POS = int(PLATINA_POS)


    TablaEstadoPlatina = [PLATINA_INICIO, PLATINA_FIN, PLATINA_ENC, PLATINA_POS, PLATINA_SET, PLATINA_MIN, PLATINA_MAX, PLATINA_FRENO, TEMP_ROBO_1,
                        FIRST_INIT_PLATINA, PLATINA_FRENO_SENSOR]

    return render_template("index.html", TablaFiltros = TablaFiltros, TablaPolarizadores = TablaPolarizadores, TablaReductores = TablaReductores,
                           TablaEstadoRueda = TablaEstadoRueda, TablaEstadoPlatina = TablaEstadoPlatina)
    '''
    return render_template("index.html", TablaFiltros = TablaFiltros, TablaPolarizadores = TablaPolarizadores, TablaReductores = TablaReductores,
                           TablaEstadoRueda = TablaEstadoRueda)


# Comandos
@app.route("/rueda1")
def rueda1():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 1")
    rueda1 = rueda.communicate(str.encode("RUEDA 1"))
    rueda.kill()
    print ("[+] RUEDA 1 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda2")
def rueda2():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 2")
    rueda1 = rueda.communicate(str.encode("RUEDA 2"))
    rueda.kill()
    print ("[+] RUEDA 2 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda3")
def rueda3():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 3")
    rueda1 = rueda.communicate(str.encode("RUEDA 3"))
    rueda.kill()
    print ("[+] RUEDA 3 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda4")
def rueda4():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 4")
    rueda1 = rueda.communicate(str.encode("RUEDA 4"))
    rueda.kill()
    print ("[+] RUEDA 4 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda5")
def rueda5():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 5")
    rueda1 = rueda.communicate(str.encode("RUEDA 5"))
    rueda.kill()
    print ("[+] RUEDA 5 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda6")
def rueda6():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 6")
    rueda1 = rueda.communicate(str.encode("RUEDA 6"))
    rueda.kill()
    print ("[+] RUEDA 6 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda7")
def rueda7():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 7")
    rueda1 = rueda.communicate(str.encode("RUEDA 7"))
    rueda.kill()
    print ("[+] RUEDA 7 OK")
    return redirect(url_for('inicio'))

@app.route("/rueda8")
def rueda8():
    rueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO RUEDA 8")
    rueda1 = rueda.communicate(str.encode("RUEDA 8"))
    rueda.kill()
    print ("[+] RUEDA 8 OK")
    return redirect(url_for('inicio'))

@app.route("/polariza1")
def polariza1():
    polariza = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO POLARIZA 1")
    polariza1 = polariza.communicate(str.encode("POLARIZA 1"))
    polariza.kill()
    print ("[+] POLARIZA 1 OK")
    return redirect(url_for('inicio'))

@app.route("/polariza2")
def polariza2():
    polariza = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO POLARIZA 2")
    polariza1 = polariza.communicate(str.encode("POLARIZA 2"))
    polariza.kill()
    print ("[+] POLARIZA 2 OK")
    return redirect(url_for('inicio'))

@app.route("/polariza3")
def polariza3():
    polariza = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO POLARIZA 3")
    polariza1 = polariza.communicate(str.encode("POLARIZA 3"))
    polariza.kill()
    print ("[+] POLARIZA 3 OK")
    return redirect(url_for('inicio'))

@app.route("/polariza4")
def polariza4():
    polariza = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO POLARIZA 4")
    polariza1 = polariza.communicate(str.encode("POLARIZA 4"))
    polariza.kill()
    print ("[+] POLARIZA 4 OK")
    return redirect(url_for('inicio'))

@app.route("/polariza5")
def polariza5():
    polariza = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO POLARIZA 5")
    polariza1 = polariza.communicate(str.encode("POLARIZA 5"))
    polariza.kill()
    print ("[+] POLARIZA 5 OK")
    return redirect(url_for('inicio'))

@app.route("/reductor1")
def reductor1():
    reductor = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO REDUCTOR 1")
    reductor1 = reductor.communicate(str.encode("REDUCTOR 1"))
    reductor.kill()
    print ("[+] REDUCTOR 1 OK")
    return redirect(url_for('inicio'))

@app.route("/reductor2")
def reductor2():
    reductor = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO REDUCTOR 2")
    reductor1 = reductor.communicate(str.encode("REDUCTOR 2"))
    reductor.kill()
    print ("[+] REDUCTOR 2 OK")
    return redirect(url_for('inicio'))

@app.route("/reductor3")
def reductor3():
    reductor = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    print ("[+] SOLICITANDO REDUCTOR 3")
    reductor1 = reductor.communicate(str.encode("REDUCTOR 3"))
    reductor.kill()
    print ("[+] REDUCTOR 3 OK")
    return redirect(url_for('inicio'))


@app.route("/platina", methods=["GET", "POST"])
def platina():
    if request.method == "GET":
        return redirect(url_for('inicio'))
    else:
        # manda a posicion de rango (0-100%)
        SetPlatina = request.form["SetPlatina"].strip()
        platina = subprocess.Popen("nc localhost 7777", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        print ("[+] SOLICITANDO PLATINA_POS " + str(SetPlatina))
        platina1 = platina.communicate(str.encode("PLATINA_POS " + SetPlatina))
        platina.kill()
        print ("[+] PLATINA_POS " + str(SetPlatina) + " OK")
        return redirect(url_for('inicio'))

@app.route("/startplatina", methods=["GET", "POST"])
def startplatina():
    if request.method == "GET":
        return redirect(url_for('inicio'))
    else:
        startplatina = subprocess.Popen("nc localhost 7777", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        print ("[+] SOLICITANDO INICIO PLATINA")
        startplatina1 = startplatina.communicate(str.encode("INICIO"))
        startplatina.kill()
        print ("[+] INICIO PLATINA OK")
        return redirect(url_for('inicio'))

@app.route("/stopplatina", methods=["GET", "POST"])
def stopplatina():
    if request.method == "GET":
        return redirect(url_for('inicio'))
    else:
        stopplatina = subprocess.Popen("nc localhost 7777", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        print ("[+] SOLICITANDO STOP PLATINA")
        stopplatina1 = stopplatina.communicate(str.encode("STOP"))
        stopplatina.kill()
        print ("[+] STOP PLATINA OK")
        return redirect(url_for('inicio'))

@app.route("/startrueda", methods=["GET", "POST"])
def startrueda():
    if request.method == "GET":
        return redirect(url_for('inicio'))
    else:
        startrueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        print ("[+] SOLICITANDO INICIO RUEDA")
        startrueda1 = startrueda.communicate(str.encode("INICIO"))
        startrueda.kill()
        print ("[+] INICIO RUEDA OK")
        return redirect(url_for('inicio'))

@app.route("/stoprueda", methods=["GET", "POST"])
def stoprueda():
    if request.method == "GET":
        return redirect(url_for('inicio'))
    else:
        stoprueda = subprocess.Popen("nc localhost 6666", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        print ("[+] SOLICITANDO STOP RUEDA")
        stoprueda1 = stoprueda.communicate(str.encode("STOP"))
        stoprueda.kill()
        print ("[+] STOP RUEDA OK")
        return redirect(url_for('inicio'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
    #app.run(debug=False, host="0.0.0.0", port=8000)
