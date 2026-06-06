#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import socket
import threading
import time


class RUCA():

    def __init__(self, call_back):

        self.numero_filtros = 8
        self.mqtt_server = '192.168.0.243'

        self.mosquitto = mqtt.Client()

        self.mosquitto.on_message = self.on_message
        self.mosquitto.on_publish = self.on_publish
        self.mosquitto.on_connect = self.on_connect
        self.mosquitto.on_disconnect = self.on_disconnect

        self.mosquitto.connect(self.mqtt_server, 1883, 60)

        self.actualiza_posicion = call_back

        self.archivo_filtros = "/home/observa/ruca_rueda1.fil"
        self.archivo_pol = "ruca_rueda2.fil"

        self.debug = False

        self.lista_filtros = []
        self.lista_pol = []

        self.lista_reductor = [
            ["Reductor Azul", 1],
            ["Reductor Rojo", 2],
            ["Sin Reductor", 3]
        ]

        self.lista_nombres_full = {}

        self.info = {}

        # Carga inicial
        self.carga_archivos()
        self.manda_nombres()


    # ==================================================
    def carga_archivos(self):

        # -------- Filtros --------
        try:
            with open(self.archivo_filtros, 'r') as f:
                self.lista_filtros = f.read().split('\n')[0:8]
        except:
            print("Error abriendo", self.archivo_filtros)
            return False

        # -------- Polarizador --------
        try:
            with open(self.archivo_pol, 'r') as f:
                self.lista_pol = f.read().split('\n')[0:5]
        except:
            print("Error abriendo", self.archivo_pol)
            return False

        # -------- Nombres --------
        self.lista_nombres_full = {}

        for i in range(8):
            self.lista_nombres_full[f"Filtro{i+1:02d}"] = self.lista_filtros[i]

        for i in range(5):
            self.lista_nombres_full[f"Polariza{i+1:02d}"] = self.lista_pol[i]

        self.lista_nombres_full['Reductor01'] = self.lista_reductor[0][0]
        self.lista_nombres_full['Reductor02'] = self.lista_reductor[1][0]
        self.lista_nombres_full['Reductor03'] = self.lista_reductor[2][0]

        print("Archivos .fil cargados")

        return True


    # ==================================================
    def recargar_filtros(self):

        print("Recargando filtros...")

        if not self.carga_archivos():
            print("Error al recargar")
            return

        self.manda_nombres()

        print("Filtros recargados OK")


    # ==================================================
    def mueve_filtros(self, pos):

        self.publica_mosquitto(
            pos,
            "oan/control/1.5m/ruca2/rueda"
        )


    def mueve_pol(self, pos):

        self.publica_mosquitto(
            pos,
            "oan/control/1.5m/ruca2/polarizador"
        )


    def mueve_reductor(self, pos):

        self.publica_mosquitto(
            pos,
            "oan/control/1.5m/ruca2/reductor"
        )


    # ==================================================
    def inicializa(self):
        #los motores de paso
        self.publica_mosquitto('INICIO')


    # ==================================================
    def envia_comando_tcp(
        self,
        host,
        port,
        comando,
        call_back,
        timeout=65.0,
        conservar_respuesta_completa=False
    ):

        def worker():

            try:
                with socket.create_connection((host, port), timeout=3.0) as conexion:
                    conexion.settimeout(timeout)
                    conexion.sendall(comando.encode("utf-8"))
                    bloques = []

                    while True:
                        bloque = conexion.recv(2048)

                        if not bloque:
                            break

                        bloques.append(bloque)

                respuesta_completa = b"".join(bloques).decode(
                    "utf-8",
                    errors="replace"
                ).strip()
                lineas = [
                    linea.strip()
                    for linea in respuesta_completa.splitlines()
                    if linea.strip() and linea.strip() != "+"
                ]
                if conservar_respuesta_completa:
                    respuesta = respuesta_completa
                else:
                    respuesta = lineas[-1] if lineas else respuesta_completa

                if respuesta:
                    call_back(True, respuesta)
                else:
                    call_back(False, "Comando enviado sin respuesta")

            except socket.gaierror:
                call_back(False, "Dirección IP o nombre de host inválido")

            except socket.timeout:
                call_back(False, "Tiempo de espera agotado")

            except ConnectionRefusedError:
                call_back(False, "Conexión rechazada por el servidor")

            except OSError as e:
                call_back(False, f"Error de conexión: {e}")

        threading.Thread(target=worker, daemon=True).start()


    # ==================================================
    def manda_nombres(self):

        msg = json.dumps(
            self.lista_nombres_full,
            separators=(',', ':'),
            sort_keys=True
        )

        print("Mandando nombres por MQTT")

        self.publica_mosquitto(
            msg,
            "oan/control/1.5m/ruca2/cambianombres"
        )


    # ==================================================
    def run(self):

        print("Iniciando loop MQTT")

        self.mosquitto.loop_start()


    # ==================================================
    def publica_mosquitto(self,msg,topic='oan/control/1.5m/ruca2/control'):

        try:
            print("MQTT >", topic, msg)
            self.mosquitto.publish(topic, msg)

        except:
            print("Error publicando MQTT")


    # ==================================================
    def on_message(self, client, userdata, message):

        try:

            jdata = message.payload.decode("utf-8")
            data = json.loads(jdata)

            self.info = data

            if self.actualiza_posicion:
                self.actualiza_posicion(self.info)

        except Exception as e:

            print("Error MQTT:", e)


    # ==================================================
    def on_connect(self, client, userdata, flags, rc):

        print("Conectado MQTT:", rc)

        self.mosquitto.subscribe(
            "oan/control/1.5m/ruca2/estado"
        )


    def on_publish(self, client, userdata, mid):

        pass


    # ==================================================
    def on_disconnect(self, client, userdata, rc):

        print("MQTT desconectado")

        while True:

            time.sleep(2)

            try:

                print("Reconectando...")
                self.mosquitto.connect(
                    self.mqtt_server, 1883, 60
                )
                break

            except:

                print("Reintento fallido")
