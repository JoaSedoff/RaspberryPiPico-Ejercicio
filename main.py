# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

# This demo publishes to topic "result" and also subscribes to that topic.
# This demonstrates bidirectional TLS communication.
# You can also run the following on a PC to verify:
# mosquitto_sub -h test.mosquitto.org -t result
# To get mosquitto_sub to use a secure connection use this, offered by @gmrza:
# mosquitto_sub -h <my local mosquitto server> -t result -u <username> -P <password> -p 8883
# Public brokers https://github.com/mqtt/mqtt.github.io/wiki/public_brokers
# red LED: ON == WiFi fail
# green LED heartbeat: demonstrates scheduler is running.

from lib.mqtt_as import MQTTClient
from lib.mqtt_local import config
import uasyncio as asyncio
from settings import SSID, password, BROKER


import machine, dht, ujson
from machine import Pin
from collections import OrderedDict
import ujson





d = dht.DHT11(machine.Pin(13))


#guardar en JSON:
def guardar_datos():
    print("Guardando parametros...")
    config = {"setpoint": setpoint, "modo":modo, "periodo": periodo}
    
    try:
        with open("config.json","w") as f:
            ujson.dump(config,f)
        print("Parametros guardados correctamente..")
    except Exception as e:
        print(f"Error al guardar parametros : {e}")



#cargar datos del JSON ya creado
def cargar_datos():
    global setpoint, modo, periodo
    try:
        with open("config.json","r") as f:
            config = ujson.load(f)
            setpoint = config.get("setpoint",20)
            modo = config.get("modo",1)
            periodo = config.get("periodo",10)
            print(config)
    except:
        print("No se encontro el JSON, usando valores por defecto")
        setpoint = 20
        modo = 1
        periodo = 10



#Parte de asyncio y mqtt

#recibir datos de los topicos suscritos
def sub_cb(topic, msg, retained):
    global setpoint, modo, periodo
    print(f"Mensaje recibido en {topic.decode()}: {msg.decode()}")
    topico = topic.decode()
    valor = msg.decode()

    if topico.endswith("/setpoint"):
        setpoint = int(valor)
        guardar_datos()
        print(f"setpoint actualizado a: {setpoint}")
    
    if topico.endswith("/modo"):
        modo = int(valor)
        guardar_datos()
        print(f"modo actualizado a: {modo}")

    if topico.endswith("/periodo"):
        periodo = int(valor)
        guardar_datos()
        print(f"periodo actualizado a: {periodo}")


#funcion para mostrar el estado de la conexión wifi (primero se debe conectar)
async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)


id = ""
for b in machine.unique_id():
  id += "{:02X}".format(b)
print(id)

#suscripcion a los topicos
async def conn_han(client):
    await client.subscribe(id +'/periodo', 1)
    print(f"Suscrito a {id + '/periodo'}")
    await client.subscribe(id +'/rele', 1)
    print(f"Suscrito a {id + '/rele'}")
    await client.subscribe(id +'/setpoint', 1)
    print(f"Suscrito a {id + '/setpoint'}")
    await client.subscribe(id +'/destello', 1)
    print(f"Suscrito a {id + '/destello'}")
    await client.subscribe(id +'/modo', 1)
    print(f"Suscrito a {id + '/modo'}")
#variables definidas por el usuario
#Main definido como una funcion asyncio

async def main(client):
    led = machine.Pin("LED", machine.Pin.OUT)  # Cambiá el número según el pin de tu placa
    await client.connect()
    n = 0
    temperatura1 = 24
    cargar_datos()
    print(f"Setpoint inicial: {setpoint}, Modo inicial:{modo}, Periodo inicial:{periodo}" )
    await asyncio.sleep(2)  # Give broker time
    while True:
        try:
            d.measure()
            try:
                temperatura=d.temperature()
                try:
                    humedad=d.humidity()
  
                except OSError as e:
                    print("sin sensor temperatura")
            except OSError as e:
                print("sin sensor humedad")
        except OSError as e:
            pass
    
        if (temperatura1 > setpoint) and (modo == 1):
            led.value(1)
            print("Temperatura alta, LED encendido") 
        else:
            led.value(0)       

        datos = ujson.dumps(OrderedDict([('temperatura',24),('humedad',53),
                                        ('setpoint',setpoint),('periodo',periodo),('modo',modo)]))
        print(f"Publicando en el topico: {config['client_id']}")
        await client.publish(config['client_id'], datos, qos = 1)
        await asyncio.sleep(periodo)  # Broker is slow





#Configuracion de MQTT
# Define configuration
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True
config['ssid'] = SSID
config['wifi_pw'] = password
config['server'] = BROKER
config['client_id'] = id.upper()
# Configurar cliente mqtt
MQTTClient.DEBUG = False  # Optional
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()