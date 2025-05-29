# Termostato MQTT con TLS

Este proyecto implementa un sistema de monitoreo y control de temperatura utilizando un microcontrolador compatible con MicroPython, un sensor DHT11 y un relé. Se comunica mediante MQTT sobre TLS para publicar datos y recibir comandos.

## Funcionalidad

- Publica temperatura y humedad medidas por el sensor DHT11.
- Controla un relé de forma automática (según setpoint) o manual.
- Recibe comandos MQTT para modificar parámetros:
  - `setpoint`
  - `modo` (1: automático, 0: manual)
  - `periodo` de publicación
  - `rele` (solo en modo manual)
  - `destello` (enciende LED integrado por unos segundos)
- Guarda los parámetros en un archivo `config.json`.

## Requisitos

- Microcontrolador con MicroPython y WiFi.
- Sensor DHT11 conectado al pin 15.
- Relé conectado al pin 28.
- MQTT broker con soporte TLS.
- Archivos necesarios en `/lib`:
  - `mqtt_as.py`
  - `mqtt_local.py`
  - `led_async.py`

## Configuración

Modificar `settings.py` con los datos de red y broker MQTT:

```python
SSID = 'tu_red_wifi'
password = 'clave_wifi'
BROKER = 'ip_o_dominio_del_broker'
