# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 13:13:42 2023

@author: JBI
"""

"""
###############################################
##Title             : client_main.py
##Description       : Main script for Domotik project
##Author            : John Bigeon   @ Github
##Date              : 20230730
##Version           : Test with 
##Usage             : MicroPython
##Script_version    : 0.0.5 (not_release)
##Output            : 
##Notes             :
###############################################
"""
###############################################
### Package
###############################################
import network
import machine
from machine import Pin, I2C, SoftI2C, ADC
import espnow
import time
import random
import utime
import ntptime
import socket
import json
import uos
import os
import re
import BME280
import BHL1750
import json

###############################################
### Class: BME280
###############################################          
class env_sensor:
    def __init__(self):
        self.i2c = SoftI2C(scl=Pin(26), sda=Pin(25), freq=10000)
        self.bme = BME280.BME280(i2c=self.i2c, address=118)

    def read(self):
        temp = float(self.bme.temperature)
        hum = float(self.bme.humidity)
        pres = float(self.bme.pressure)
        return {'val_temp': temp, 'val_hum': hum, 'val_pres' : pres}
    

###############################################
### Class: BH1750
###############################################          
class lux_sensor:
    def __init__(self):
        #self.i2c = SoftI2C(scl=Pin(33), sda=Pin(32))
        self.i2c = I2C(1, scl=Pin(33), sda=Pin(32))
        self.bh1750 = BHL1750.BH1750(0x23, self.i2c)

    def read(self):
        lux = float(self.bh1750.measurement)
        return {'lux': lux}


###############################################
### Class: Battery
###############################################
class battery:
    def __init__(self):
        self.adc = ADC(Pin(34))
        self.adc.atten(ADC.ATTN_11DB) #Full range: 3.3v
        self.R1 = 2000 # Ohm
        self.R2 = 6800 # Ohm
        
    def read(self):
        val_digit = self.adc.read_u16()
        Vout=3.3*(val_digit/65535)
        Vin = Vout * (self.R1 + self.R2) / self.R2
        return {'val_bat': Vin}


###############################################
### Function: extract the mac address
############################################### 
def mac_str_to_bytes(mac_str):
    hex_list = mac_str.split(':')
    return bytes([int(h, 16) for h in hex_list])


###############################################
### Power management part
############################################### 
## Via https://docs.micropython.org/en/latest/esp8266/tutorial/powerctrl.html
## https://forum.micropython.org/viewtopic.php?t=3555
# Reduce the CPU frequency
machine.freq(80000000)
freq_machine = machine.freq()
print(f'Machine running at {freq_machine}')

## Configure RTC.ALARM0 to be able to wake the device
# Not working with esp32
# rtc = machine.RTC()
# rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)

# Set RTC.ALARM0 to fire after 10 seconds (waking the device)
# rtc.alarm(rtc.ALARM0, 10000)

###############################################
### Set up Wi-Fi and ESPNow
###############################################
# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()   # Because ESP8266 auto-connects to last Access Point

e = espnow.ESPNow()
e.active(True)


###############################################
### Set up mac address
############################################### 
# How to get the mac address
mac_address = network.WLAN().config('mac')
sender_mac = ':'.join('%02x' % b for b in mac_address)

# Define the receiver's MAC address
receiver_mac = 'a1:b1:c1:d1:e1:f1'

receiver_mac_bytes = mac_str_to_bytes(receiver_mac)

e.add_peer(receiver_mac_bytes)      # Must add_peer() before send()


###############################################
### TODEBUG
############################################### 
led_pin = Pin(2, Pin.OUT)


###############################################
### Main
###############################################
if __name__ == "__main__":
    env_sens = env_sensor()
    lux_sensor = lux_sensor()
    bat_sensor = battery()
    while True:
            # Create a message to send
            msg = {"Loc": sender_mac, "Prob": ["Tmp", "Hum", "Prs", "Lux", "Bat"], "Value": [env_sens.read()['val_temp'],
                                                                                             env_sens.read()['val_hum'],
                                                                                             env_sens.read()['val_pres'],
                                                                                             lux_sensor.read()['lux'],
                                                                                             bat_sensor.read()['val_bat']
                                                                                             ]}
            
            #msg = {"Loc": sender_mac, "Prob": ["Tmp", "Hum", "Prs", "Lux", "Bat"], "Value": [random.randint(10, 30),
            #                                                                                 random.randint(10, 100),
            #                                                                                 random.randint(10, 1000),
            #                                                                                 random.randint(10, 1000),
            #                                                                                 random.randint(0, 100)
            #                                                                                 ]}
            
            # Send the message to the receiver
            print(msg)
            e.send(receiver_mac_bytes, json.dumps(msg))
            print("Sent message to", receiver_mac, ":", msg)
            #time.sleep(2.0)
            led_pin.on()    # Turn on the LED
            print('heey')
            time.sleep(0.5)   # Wait for 1 second
            led_pin.off()   # Turn off the LED
            time.sleep(0.5)   # Wait for 1 second
            
            # put the device to sleep (ms)
            machine.deepsleep(60*1000)

