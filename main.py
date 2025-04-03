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
from lib.led_async import LED_async  # Class as listed above




d = dht.DHT11(machine.Pin(15))

#guardar en JSON:
def guardar_datos():
    global setpoint,modo,periodo,rele
    config = {"setpoint": setpoint, "modo":modo, "periodo": periodo, "rele":rele}
    try:
        with open("config.json","w") as f:
            ujson.dump(config,f)
    except Exception as e:
        print(f"Error al guardar parametros : {e}")



#cargar datos del JSON ya creado
def cargar_datos():
    global setpoint, modo, periodo, rele
    try:
        with open("config.json","r") as f:
            config = ujson.load(f)
            setpoint = config.get("setpoint",20)
            modo = config.get("modo",1)
            periodo = config.get("periodo",10)
            rele = config.get("rele",1)
            print(config)
    except:
        print("No se encontro el JSON, usando valores por defecto")
        setpoint = 20
        modo = 1
        periodo = 10
        rele = 1


async def destellar():
    global band
    led = machine.Pin("LED", machine.Pin.OUT)
    
    for i in range(10):  
        led.toggle()
        await asyncio.sleep(0.5)  
    
    led.value(0)  
    band = False  

#Parte de asyncio y mqtt

#recibir datos de los topicos suscritos
def sub_cb(topic, msg, retained):
    global setpoint, modo, periodo,rele, destello, band
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

    if topico.endswith("/rele"):
        rele = int(valor)
        guardar_datos()
        print(f"orden rele vale {rele} ")

    if topico.endswith("/destello"):
        destello = int(valor)
        if destello: 
            band = True

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
    await client.subscribe(id +'/destello', 1)
    print(f"Suscrito a {id + '/destello'}")


#Main definido como una funcion asyncio

async def main(client):
    led = machine.Pin("LED", machine.Pin.OUT) 
    led.value(0)
    temperatura = 24
    humedad = 53
    global band
    band = False
    await client.connect()
    relay = machine.Pin(28,machine.Pin.OUT) #pin del rele
    relay.value(1) #empieza en 1 (para el opto sería un bajo)
    cargar_datos() #si hay un JSON ya creado lo lee
    print(f"Setpoint inicial: {setpoint}, Modo inicial:{modo}, Periodo inicial:{periodo}, Estado de rele: {rele}") #informa valores del JSON leido
    await asyncio.sleep(2) #tiempo para poder conectarse al broker
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
            print("sin sensor")
    
        if (temperatura > setpoint) and (modo == 1): #en modo automatico el estado del rele depende de la temperatura y setpoint
            relay.value(0)
            print("Temperatura alta, rele encendido") 
        else:
            relay.value(1)       

        if (modo == 0): #si esta en modo manual, el estado del rele depende unicamente de la variable rele
            if rele: 
                relay.value(0)
                print("Modo manual, encendiendo rele")
            else: 
                relay.value(1)
                print("Modo manual, apagando rele")

        if band:
            print("Orden de destello recibida")
            band = False
            asyncio.create_task(destellar())

        datos = ujson.dumps(OrderedDict([('temperatura',temperatura),('humedad',humedad),
                                        ('setpoint',setpoint),('periodo',periodo),('modo',modo)]))
        print(f"Publicando en el topico: {config['client_id']}")
        await client.publish(config['client_id'], datos, qos = 1)
        await asyncio.sleep(periodo)  # Broker is slow





#Configuracion de MQTT
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True
config['ssid'] = SSID
config['wifi_pw'] = password
config['server'] = BROKER
config['client_id'] = id.upper() #pasa a mayusculas el id por el topico suscrito

# Configurar cliente mqtt
MQTTClient.DEBUG = False  # Optional
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()