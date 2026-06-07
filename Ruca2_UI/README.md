# RUCA2 UI

Interfaz gráfica de escritorio para operar y diagnosticar la rueda de filtros
RUCA2. Está desarrollada en Python 3, GTK 3 y Glade.

La versión actual de la interfaz es **2.3**.

## Arquitectura

La interfaz utiliza dos canales de comunicación:

| Canal | Uso |
| --- | --- |
| MQTT | Operación normal, nombres de filtros y recepción continua de estado. |
| TCP directo | Comandos y diagnóstico desde la pestaña Ingeniería. |

Configuración predeterminada:

```text
Broker MQTT:        192.168.0.243:1883
Servidor de rueda:  192.168.0.34:6666
Tópico de estado:   oan/control/1.5m/ruca2/estado
```

`Ruca2_mqtt_status.py` consulta `ESTADO` al servidor y publica el resultado por
MQTT aproximadamente cada 2 segundos. La interfaz recibe esos mensajes para
actualizar los indicadores normales.

## Archivos

| Archivo | Función |
| --- | --- |
| `ruca2.py` | Controlador principal GTK y lógica de la interfaz. |
| `ruca2.glade` | Definición visual de ventanas, pestañas y controles. |
| `AYUDA.md` | Guía breve mostrada dentro de la pestaña Ayuda. |
| `c_filtros_ruca2_mqtt.py` | Comunicación MQTT y cliente TCP asíncrono. |
| `runme.sh` | Reinicia y ejecuta la interfaz desde su directorio instalado. |
| `ruca_rueda1.fil` | Ejemplo local de nombres para la rueda de filtros. |

La interfaz debe ejecutarse desde el directorio `Ruca2_UI`, porque carga
`ruca2.glade` usando una ruta relativa.

## Pestaña Main

La pestaña principal está destinada a la operación habitual:

- **Inicializa Ruedas** solicita confirmación y publica `INICIO` por MQTT.
- El selector de filtros publica la posición deseada en
  `oan/control/1.5m/ruca2/rueda`.
- El selector de reductores publica la posición en
  `oan/control/1.5m/ruca2/reductor`.
- **Publicar lista de filtros** solicita confirmación, vuelve a leer los
  archivos `.fil` y publica los nombres actualizados.
- Los campos de filtro actual, switch y estado se actualizan con los mensajes
  recibidos en `oan/control/1.5m/ruca2/estado`.

Archivos de nombres configurados actualmente:

```text
Filtros:       /home/observa/ruca_rueda1.fil
Polarizadores: ruca_rueda2.fil
```

## Pestaña Ayuda

La pestaña Ayuda carga `AYUDA.md` cada vez que se abre. El contenido se
presenta con formato visual ligero para encabezados, listas y bloques de
código, sin requerir dependencias Markdown adicionales.

Si el archivo no existe o no puede leerse, la pestaña muestra el detalle del
error. La interfaz debe ejecutarse desde `Ruca2_UI` para encontrar el archivo.

## Pestaña Ingeniería

La pestaña Ingeniería se comunica directamente con `Ruca2_rueda.py` mediante
TCP. La dirección IP y el puerto son editables.

Cada vez que se intenta entrar, la interfaz muestra un aviso indicando que la
pestaña es de uso exclusivo del personal técnico académico de soporte. Si el
usuario cancela, permanece en la pestaña anterior.

Las operaciones TCP se ejecutan en un hilo para no bloquear GTK. Mientras un
comando está activo, los controles de Ingeniería permanecen deshabilitados.

### Velocidad, paro e inicialización

| Control | Comando |
| --- | --- |
| Aplicar velocidad | Solicita confirmación y envía `SPEED <rpm>`, limitado a `1..100 RPM`. |
| STOP | `STOP`, con confirmación. |
| INICIO | `INICIO`, con confirmación. |

La **velocidad actual** se actualiza normalmente desde MQTT. Después de aplicar
`SPEED`, también se actualiza inmediatamente si el servidor responde `OK`.

### Diagnóstico directo

**Actualizar estado directo** envía `ESTADO` por TCP y muestra:

- Indicador verde o rojo de comunicación directa.
- Hora de la última lectura válida.
- Tabla desplazable con todas las variables devueltas por el servidor.

La tabla agrupa las variables en:

- Estado general.
- Posiciones y destinos.
- Inicialización.
- Frenos y sensores.
- Contadores, switches y botones físicos.

Colores principales:

| Color | Significado |
| --- | --- |
| Azul | Índices, destinos y velocidad. |
| Verde | Estado saludable o mecanismo inicializado. |
| Amarillo | Estado que requiere atención. |
| Rojo | Error, paro de emergencia o fallo de comunicación. |

Después de un comando exitoso de Ingeniería, la interfaz solicita
automáticamente `ESTADO` para confirmar el resultado.

### Frenos

Los botones afectan simultáneamente a rueda, polarizador y reductor:

| Acción visible | Comando | Comportamiento del servidor |
| --- | --- | --- |
| Aplicar frenos | `FRENOS 1` | Coloca las salidas en `LOW` y bloquea. |
| Liberar frenos | `FRENOS 0` | Coloca las salidas en `HIGH` y libera. |

Liberar los frenos requiere confirmación.

### Movimiento manual

El panel `MUEVE` permite seleccionar:

| Campo | Valores |
| --- | --- |
| Motor | Rueda `1`, polarizador `2`, reductor `3`. |
| Dirección | Atrás `0`, adelante `1`. |
| Pasos | Entero entre `1` y `500`. |

El comando generado es:

```text
MUEVE <motor> <pasos> <dirección>
```

Todo movimiento manual requiere confirmación antes de enviarse.

## Pestaña About

Muestra la versión actual y el historial resumido de cambios de la interfaz.

El orden de pestañas es:

```text
Main | Ayuda | About | Ingeniería
```

## Instalación

Dependencias principales:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0
python3 -m pip install paho-mqtt
```

También deben estar disponibles:

- El broker MQTT configurado.
- `Ruca2_mqtt.py` para traducir los controles MQTT.
- `Ruca2_mqtt_status.py` para publicar estado periódico.
- `Ruca2_rueda.py` escuchando comandos TCP en el puerto `6666`.

## Ejecución

Desde el directorio de la interfaz:

```bash
cd /home/observa/cadena/Ruca2_UI
./ruca2.py
```

También puede utilizarse:

```bash
./runme.sh
```

`runme.sh` detiene instancias anteriores de `ruca2.py`, cambia al directorio
configurado y ejecuta una nueva instancia.

## Validación

Validar sintaxis Python y XML Glade:

```bash
python3 -m py_compile ruca2.py c_filtros_ruca2_mqtt.py
xmllint --noout ruca2.glade
```

Pruebas manuales recomendadas:

1. Confirmar que Main recibe cambios desde el tópico MQTT de estado.
2. Usar **Actualizar estado directo** y comprobar el indicador verde.
3. Aplicar una velocidad segura y confirmar su valor en la tabla.
4. Verificar las confirmaciones de `STOP`, `INICIO`, liberar frenos y `MUEVE`.
5. Probar una IP o puerto inválido y comprobar que GTK continúa respondiendo.

## Seguridad

- La pestaña Ingeniería controla hardware real directamente.
- `STOP` activa el paro de emergencia; para recuperar debe ejecutarse `INICIO`.
- `FRENOS 0` libera los tres mecanismos simultáneamente.
- `MUEVE` realiza movimientos manuales sin posicionamiento automático.
- Antes de liberar frenos o mover un motor, verificar físicamente que el
  mecanismo esté libre y sea seguro operarlo.

## Repositorio

<https://github.com/baja2k9/Ruca2>
