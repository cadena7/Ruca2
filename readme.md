# RUCA 2.0

RUCA 2.0 es el software de control para la rueda de filtros, rueda de polarizadores, reductores focales y platina giratoria del instrumento RUCA. El sistema corre en una Raspberry Pi 3 y expone control por sockets TCP locales, una interfaz web Flask/Gunicorn y un puente MQTT para operación remota.

El código controla hardware real por GPIO, motores a pasos mediante Adafruit MotorHAT, frenos por solenoides y una platina con RoboClaw. Antes de operar motores, verifica límites, frenos, alimentación y que no haya riesgo mecánico.

## Componentes principales

| Archivo | Funcion |
| --- | --- |
| `Ruca2_rueda.py` | Servidor principal de rueda de filtros, polarizador y reductores. Escucha comandos TCP en el puerto `6666`. |
| `Ruca2_platina.py` | Servidor de platina giratoria. Escucha comandos TCP en el puerto `7777`. |
| `Ruca2_GUI.py` | Interfaz web Flask para operar RUCA desde navegador. |
| `Ruca2_mqtt.py` | Puente MQTT: recibe topicos de control y los traduce a comandos socket locales. |
| `Ruca2_mqtt_status.py` | Publicador periodico de estado por MQTT. |
| `Ruca2_variables.py` | Clases de variables globales para rueda y platina. |
| `filtros.json` | Nombres configurables de filtros, polarizadores y reductores. |
| `reinicio_ruca.py` | Reinicia Supervisor todos los dias a las 09:00. |
| `templates/` | Plantillas HTML de la interfaz web. |
| `static/` | CSS, JS, fuentes e imagenes de la interfaz web. |
| `Instalador en Raspi/` | Configuraciones de Supervisor, Nginx y notas de instalacion en Raspberry Pi. |

## Servicios y puertos

| Servicio | Puerto | Protocolo |
| --- | --- | --- |
| Rueda / polarizador / reductores | `6666` | TCP socket, comandos de texto |
| Platina | `7777` | TCP socket, comandos de texto |
| GUI web | `8000` directo o `80` via Nginx | HTTP |
| MQTT | Broker `192.168.0.243` | Topicos `oan/control/1.5m/ruca2/#` |

## Comandos socket de rueda

Ejemplos usando `nc`:

```bash
echo INICIO | nc localhost 6666
echo ESTADO | nc localhost 6666
echo RUEDA 2 | nc localhost 6666
echo POLARIZA 3 | nc localhost 6666
echo REDUCTOR 1 | nc localhost 6666
echo SPEED 80 | nc localhost 6666
echo MUEVE 1 100 1 | nc 192.168.0.34 6666
echo STOP | nc localhost 6666
echo FRENOS 0 | nc localhost 6666
```

Comandos disponibles:

| Comando | Descripcion |
| --- | --- |
| `INICIO` | Inicializa la rueda de filtros y reductores. |
| `ESTADO` | Devuelve estado en JSON. |
| `NOMBRE` | Devuelve nombres de filtros, polarizadores y reductores. |
| `RUEDA 1..8` | Mueve la rueda al filtro indicado. |
| `POLARIZA 1..5` | Mueve la rueda de polarizadores. |
| `REDUCTOR 1..3` | Posiciona reductor azul, rojo o vacio. |
| `SPEED <rpm>` | Ajusta velocidad de la rueda. |
| `MUEVE <motor> <pasos> <dir>` | Movimiento manual de motor. |
| `STOP` | Paro de emergencia y bloqueo hasta `INICIO`. |
| `FRENOS 0/1` | Activa o libera frenos segun la logica del programa. |

## Comandos socket de platina

```bash
echo INICIO | nc localhost 7777
echo ESTADO | nc localhost 7777
echo PLATINA_POS 50 | nc localhost 7777
echo PLATINA_ENC 10000 | nc localhost 7777
```

La platina esta marcada en el codigo como clausurada/reducida en versiones recientes, asi que revisar mecanica y configuracion antes de reactivarla.

## MQTT

El puente MQTT usa:

```text
Broker: 192.168.0.243
Base:   oan/control/1.5m/ruca2
```

Ejemplos:

```bash
mosquitto_sub -h 192.168.0.243 -t 'oan/control/1.5m/ruca2/#' -d
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/control -m INICIO
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/control -m ESTADO
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/rueda -m 5
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/polarizador -m 2
mosquitto_pub -h 192.168.0.243 -t oan/control/1.5m/ruca2/reductor -m 1
```

Topicos principales:

| Topico | Uso |
| --- | --- |
| `oan/control/1.5m/ruca2/control` | `INICIO`, `STOP`, `ESTADO`, `NOMBRES`. |
| `oan/control/1.5m/ruca2/rueda` | Posicion de filtro `1..8`. |
| `oan/control/1.5m/ruca2/polarizador` | Posicion de polarizador `1..5`. |
| `oan/control/1.5m/ruca2/reductor` | Posicion de reductor `1..3`. |
| `oan/control/1.5m/ruca2/estado` | Estado JSON retenido. |
| `oan/control/1.5m/ruca2/nombres` | Nombres JSON retenidos. |
| `oan/control/1.5m/ruca2/cambianombres` | Actualiza nombres via JSON. |

## Botones fisicos GPIO

`Ruca2_rueda.py` lee cuatro botones nuevos:

| Variable | GPIO BCM | Funcion actual |
| --- | --- | --- |
| `B_START` | `7` | Envia `STOP` y luego `INICIO` por socket local. |
| `B_STOP` | `21` | Envia `STOP` por socket local. |
| `B_UP` | `9` | Mueve a filtro actual + 1, con vuelta `8 -> 1`. |
| `B_DOWN` | `10` | Mueve a filtro actual - 1, con vuelta `1 -> 8`. |

Estas variables tambien viajan en los diccionarios de estado de `Ruca2_rueda.py`, se republican por `Ruca2_mqtt.py` y se muestran en la GUI.

## Estado JSON

El comando `ESTADO` de la rueda devuelve variables como:

- Posiciones: `RUEDA_INDICE`, `POLARIZA_INDICE`, `REDUCTOR_INDICE`
- Setpoints: `RUEDA_INDICE_SET`, `POLARIZA_INDICE_SET`, `REDUCTOR_SET`
- Inicializacion: `FIRST_INIT_RUEDA`, `FIRST_INIT_POLARIZA`, `FIRST_INIT_REDUCTOR`
- Frenos y sensores: `RUEDA_FRENO`, `RUEDA_FRENO_SENSOR`, `POLARIZA_FRENO`, `POLARIZA_FRENO_SENSOR`, `REDUCTOR_FRENO`
- Estado: `RUEDA_ESTADO`, `RUEDA_PARO_EMERGENCIA`, `RUEDA_SWITCH`, `RUEDA_SPEED`
- Botones: `B_START`, `B_STOP`, `B_UP`, `B_DOWN`

## Configuracion de nombres

Los nombres de filtros y posiciones se guardan en `filtros.json`:

```json
{
  "FILTRO01": "VACIO",
  "FILTRO02": "ESPACIO 02",
  "POLARIZA01": "VACIO",
  "REDUCTOR01": "AZUL"
}
```

El servidor de rueda los carga al arrancar. Tambien existe el comando/topico para cambiar nombres y persistirlos.

## Instalacion y arranque en Raspberry Pi

El arbol `Instalador en Raspi/` contiene configuraciones listas para despliegue. La configuracion de Supervisor espera el proyecto en:

```text
/home/pi/Documents/Ruca
```

Programas configurados:

| Supervisor program | Comando |
| --- | --- |
| `GUI` | `gunicorn Ruca2_GUI:app -k gevent -t 150 -w 4 -b 0.0.0.0:8000` |
| `rueda` | `python3 Ruca2_rueda.py` |
| `platina` | `python3 Ruca2_platina.py` |
| `mqtt_control` | `python3 Ruca2_mqtt.py` |
| `mqtt_status` | `python3 Ruca2_mqtt_status.py` |
| `reinicio_automatico` | `python3 reinicio_ruca.py` |

Comandos tipicos:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
sudo supervisorctl restart rueda
sudo supervisorctl restart GUI
```

Nginx puede publicar la GUI en puerto `80` y reenviar a Gunicorn en `127.0.0.1:8000`.

## Desarrollo y pruebas

Validar sintaxis:

```bash
python3 -m py_compile Ruca2_rueda.py Ruca2_platina.py Ruca2_mqtt.py Ruca2_GUI.py
```

Prueba rapida de movimiento aleatorio de filtros:

```bash
./test_ruca.sh
```

Pruebas manuales recomendadas despues de cambios:

1. `echo ESTADO | nc localhost 6666`
2. `echo INICIO | nc localhost 6666`
3. `echo RUEDA 1 | nc localhost 6666`
4. `echo STOP | nc localhost 6666`
5. Revisar estado MQTT retenido en `oan/control/1.5m/ruca2/estado`
6. Abrir la GUI y confirmar que las variables se muestran correctamente

## Dependencias conocidas

El proyecto usa, entre otras:

- Python 3
- `RPi.GPIO`
- `simplejson`
- `paho-mqtt`
- `Flask`
- `gunicorn`
- `gevent`
- `schedule`
- `netcat` / `nc`
- Supervisor
- Nginx
- Librerias locales `Adafruit_MotorHAT/` y `pyroboclaw/`

Algunas dependencias empaquetadas o notas de instalacion estan dentro de `Instalador en Raspi/`.

## Notas de seguridad y mantenimiento

- `STOP` deja la rueda en paro de emergencia; para recuperar, ejecutar `INICIO`.
- Revisar fisicamente frenos, sensores y switches antes de probar movimientos.
- No ejecutar pruebas de movimiento si la rueda no esta libre mecanicamente.
- `reinicio_ruca.py` recarga Supervisor diariamente a las 09:00.
- `backup/` contiene copias historicas de scripts principales; no se usan como entrada principal de ejecucion.
