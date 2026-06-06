# Ayuda de RUCA2 UI

RUCA2 UI permite operar la rueda de filtros y consultar el estado del instrumento.

## Pestaña Main

- **Inicializa Ruedas** inicia la búsqueda de posición inicial después de confirmar.
- Seleccione un filtro o reductor para enviar la posición por MQTT.
- **Publicar lista de filtros** relee los archivos `.fil` y publica sus nombres.
- Los campos de filtro, switch y estado se actualizan desde MQTT.

## Estados y colores

- **Verde:** estado saludable o comunicación correcta.
- **Azul:** índices, destinos y velocidad.
- **Amarillo:** condición que requiere atención.
- **Rojo:** error, paro de emergencia o falta de comunicación.

## Pestaña Ingeniería

Ingeniería es de uso exclusivo del personal técnico académico de soporte.

- **Actualizar estado directo** consulta `ESTADO` mediante TCP.
- **Aplicar velocidad** envía `SPEED` entre 1 y 100 RPM.
- **STOP** activa el paro de emergencia.
- **INICIO** recupera e inicializa los mecanismos.
- **Aplicar frenos** bloquea los tres mecanismos.
- **Liberar frenos** libera los tres mecanismos.
- **MOVER** realiza movimiento manual entre 1 y 500 pasos.

### Advertencias

- Verifique físicamente que el mecanismo esté libre antes de liberar frenos o mover.
- `MUEVE` no realiza posicionamiento automático.
- Después de `STOP` debe ejecutar `INICIO` para recuperar la operación.

## Solución rápida de problemas

- Si Main no actualiza, revise el broker MQTT `192.168.0.243`.
- Si Ingeniería indica **Sin comunicación**, revise la IP y el puerto TCP.
- La dirección predeterminada del servidor es:

```text
192.168.0.34:6666
```

- Use **Actualizar estado directo** para confirmar comunicación con `Ruca2_rueda.py`.
