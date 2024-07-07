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
##Usage             : MicroPython (esp32-20220618-v1.19.1)
##Script_version    : 0.0.5 (not_release)
##Output            :
##Notes             :
###############################################
"""
###############################################
### Package
###############################################
import network
from machine import Pin
import espnow
import json
import time

###############################################
### Function: extract the mac address
###############################################
def mac_str_to_bytes(mac_str):
    hex_list = mac_str.split(':')
    return bytes([int(h, 16) for h in hex_list])


###############################################
### Set up Wi-Fi and ESPNow
###############################################
# Set up Wi-Fi and ESPNow
# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)
#sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()   # Because ESP8266 auto-connects to last Access Point

e = espnow.ESPNow()
e.active(True)

###############################################
### Set up mac address
###############################################
# How to get the mac address
mac_address = network.WLAN().config('mac')
receiv_mac = ':'.join('%02x' % b for b in mac_address)

# Define the sender's MAC address
sender_mac = 'a2:b2:c2:d2:e2:f2'

sender_mac_bytes = mac_str_to_bytes(sender_mac)

e.add_peer(sender_mac_bytes)


###############################################
### Main
###############################################
while True:
    host, msg = e.recv(timeout_ms=5000)
    #print(host)
    if msg is None:
        print('Message not received')
    else:
        if msg:             # msg == None if timeout in recv()
            print(msg)
            # Parse the received JSON string
            #parsed_data = json.loads(msg)
            

            ## Extract the probe names and values
            #sender_mac = parsed_data["Loc"]
            #probe_names = parsed_data["Prob"]
            #probe_values = parsed_data["Value"]

            ## Print the results
            #print("Sender MAC:", sender_mac)
            #for name, value in zip(probe_names, probe_values):
                #print(f"{name}: {value}")

            if msg == b'end':
                break
            
    time.sleep(2.0)
