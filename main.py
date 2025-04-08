# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

# demo que publica y recibe mensajes por mqtt con tls

from lib.mqtt_as import MQTTClient
from lib.mqtt_local import config
import uasyncio as asyncio
from settings import SSID, password, BROKER
import machine, dht, ujson
from machine import Pin
from collections import OrderedDict
from lib.led_async import LED_async

d = dht.DHT11(machine.Pin(15))

# guardar json con los datos
def guardar_datos():
    global setpoint, modo, periodo, rele
    datos = {"setpoint": setpoint, "modo": modo, "periodo": periodo, "rele": rele}
    try:
        with open("config.json", "w") as f:
            ujson.dump(datos, f)
    except Exception as e:
        print(f"error al guardar: {e}")

# leer json si ya existe
def cargar_datos():
    global setpoint, modo, periodo, rele
    try:
        with open("config.json", "r") as f:
            config = ujson.load(f)
            setpoint = config.get("setpoint", 20)
            modo = config.get("modo", 1)
            periodo = config.get("periodo", 10)
            rele = config.get("rele", 1)
            print(config)
    except:  #se establecen valores por defecto cuando no se puede leer el json
        print("no se encontró el json, usando valores por defecto")
        setpoint = 20
        modo = 1
        periodo = 10
        rele = 1

# destello de led
async def destellar():
    global band
    led = Pin("LED", Pin.OUT)
    for _ in range(10):
        led.toggle()
        await asyncio.sleep(0.5)
    led.value(0)
    band = False

# manejar mensajes recibidos
def sub_cb(topic, msg, retained):
    global setpoint, modo, periodo, rele, band
    print(f"mensaje recibido en {topic.decode()}: {msg.decode()}")
    topico = topic.decode()
    valor = msg.decode()
    #se almacenan los datos en un json con la funcion guardar_datos
    if topico.endswith("/setpoint"):
        setpoint = int(valor)
        guardar_datos()
        print(f"setpoint actualizado: {setpoint}")

    elif topico.endswith("/modo"):
        modo = int(valor)
        guardar_datos()
        print(f"modo actualizado: {modo}")

    elif topico.endswith("/periodo"):
        periodo = int(valor)
        guardar_datos()
        print(f"periodo actualizado: {periodo}")

    elif topico.endswith("/rele"):
        rele = int(valor)
        guardar_datos()
        print(f"rele actualizado: {rele}")

    elif topico.endswith("/destello") and int(valor): #el valor de destello no se almacena de forma volátil
        band = True

# wifi conectado o desconectado
async def wifi_han(state):
    print('wifi', 'conectado' if state else 'desconectado')
    await asyncio.sleep(1)

# obtener id del dispositivo
id = "".join("{:02X}".format(b) for b in machine.unique_id())
print(id)

# suscripciones mqtt
async def conn_han(client): #se suscribe a todos los topicos 
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
    await client.subscribe(id +'/destello', 1)
    print(f"Suscrito a {id + '/destello'}")

# loop principal
async def main(client):
    global band
    band = False
    led = Pin("LED", Pin.OUT) #led integrado en la placa, se usa para destello
    led.value(0)# el led comienza apagado

    await client.connect()
    relay = Pin(28, Pin.OUT)
    relay.value(1)

    cargar_datos() #lee json
    print(f"setpoint: {setpoint}, modo: {modo}, periodo: {periodo}, rele: {rele}") #muestra los datos iniciales
    await asyncio.sleep(2)

    while True:
        try:
            d.measure() #sensa la temperatura y humedad con el dht
            temperatura = d.temperature()
            humedad = d.humidity()
        except OSError:
            print("error con el sensor")

        if modo == 1: #si el modo es automatico, el estado del rele depende de la temperatura y el setpoint
            if temperatura > setpoint:
                relay.value(0)
                print("temp alta, encendiendo rele")
            else:
                relay.value(1)
        else: #en modo manual, el estado del rele depende unicamente de la variable rele
            if rele:
                relay.value(0)
                print("modo manual, encendiendo rele")
            else:
                relay.value(1)
                print("modo manual, apagando rele")


        if band: #la orden de destello se maneja con una variable global
            print("orden de destello recibida") 
            band = False
            asyncio.create_task(destellar())

        datos = ujson.dumps(OrderedDict([
            ('temperatura', temperatura),
            ('humedad', humedad),
            ('setpoint', setpoint),
            ('periodo', periodo),
            ('modo', modo)
        ]))
        print(f"publicando en: {config['client_id']}")
        await client.publish(config['client_id'], datos, qos=1)
        await asyncio.sleep(periodo)

# config mqtt
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True
config['ssid'] = SSID
config['wifi_pw'] = password
config['server'] = BROKER
config['client_id'] = id.upper() #pasa a mayúsculas el ID por el tópico suscrito en MQTTx

# crear cliente mqtt
MQTTClient.DEBUG = False
client = MQTTClient(config)

try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()
