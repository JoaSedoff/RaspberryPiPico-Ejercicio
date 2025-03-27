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


d = dht.DHT11(machine.Pin(13))


#Parte de asyncio y mqtt

def sub_cb(topic, msg, retained):
    print('Topic = {} -> Valor = {}'.format(topic.decode(), msg.decode()))

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
    await client.subscribe(id +'periodo', 1)
    await client.subscribe(id +'rele', 1)
    await client.subscribe(id +'setpoint', 1)
    await client.subscribe(id +'destello', 1)
    await client.subscribe(id +'modo', 1)
#variables definidas por el usuario

modo = 0
setpoint = 20
periodo = 10



#Main definido como una funcion asyncio

async def main(client):
    await client.connect()
    n = 0
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
            print("sin sensor")

        if ((d.temperature()>setpoint) and (modo == 1)): rele = 1
        else: rele = 0
        

        datos = ujson.dumps(OrderedDict([('temperatura',24),('humedad',53),
                                        ('setpoint',setpoint),('periodo',periodo),('modo',modo)]))
        
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

# Configurar cliente mqtt
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()