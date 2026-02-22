#!/usr/bin/env python
import os
import schedule
import time


def reload_supervisor():
    # Ejecuta el comando con privilegios de superusuario
    os.system("sudo supervisorctl reload")


# Programa la tarea para que se ejecute cada 1 días a las 09:00 PST
schedule.every(1).days.at("09:00").do(reload_supervisor)

# Imprime un mensaje indicando que el script ha iniciado correctamente
print("El script ha iniciado correctamente y se ejecutará cada 1 días a las 09:00 PST.")

while True:
    # Ejecuta las tareas programadas
    schedule.run_pending()
    time.sleep(30)