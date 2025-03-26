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


# Germán Andrés Xander 2024
import machine
from machine import Pin
import dht

from mqtt_as import MQTTClient
from mqtt_local import wifi_led, blue_led, config
import asyncio
from primitives import Broker



d = dht.DHT11(Pin(15))
d.measure()
temperatura=d.temperature()
print(f"\nla temperatura actual es de {temperatura} C")
humedad=d.humidity()
print(f"la humedad actual es de {humedad} %")


id = ""
for b in machine.unique_id():
  id += "{:02X}".format(b)
print(id)

