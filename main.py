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

from rich import print
from lib.mqtt_as import MQTTClient
from lib.mqtt_local import config
import uasyncio as asyncio
from settings import SSID, password, BROKER


import machine
from machine import Pin
import dht

#Parte de asyncio y mqtt

#Funcion para imprimir un mensaje recibido mediante mqtt
def sub_cb(topic, msg, retained):
    print('Topic = {} -> Valor = {}'.format(topic.decode(), msg.decode()))



#funcion para mostrar el estado de la conexión wifi (primero se debe conectar)
async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

#suscripcion a los topicos de temperatura y humedad (mqtt)
async def conn_han(client):
    await client.subscribe('topico/temperatura', 1)
    await client.subscribe('topico/humedad', 1)


#Main definido como una funcion asyncio

async def main(client):
    await client.connect()
    n = 0
    setpoint = 0
    modo = 0
    rele = 0
    await asyncio.sleep(2)  # Give broker time
    while True:
        try:
            d.measure()
            try:
                temperatura=d.temperature()
                await client.publish('topico/temperatura', '{}'.format(temperatura), qos =  1) #Manda mensaje MQTT con la temperatura al topico temperatura
            except OSError as e:
                print("sin sensor temperatura")
            try:
                humedad=d.humidity()
                await client.publish('topico/humedad', '{}'.format(humedad), qos = 1) #Manda mensaje MQTT con la humedad al topico humedad
            except OSError as e:
                print("sin sensor humedad")
        except OSError as e:
            print("sin sensor")
        
        await client.publish('topico/setpoint', '{}'.format(setpoint), qos =  1)

        if (temperatura > setpoint): rele = 1
        await client.publish('topico/rele', '{}'.format(rele), qos =  1)

        


                 
        await asyncio.sleep(20)  # Broker is slow


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





#Codigo para saber el ID del ESP32
id = ""
for b in machine.unique_id():
  id += "{:02X}".format(b)
print(id)

