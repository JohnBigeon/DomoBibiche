# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 13:13:42 2023

@author: JBI
"""

"""
###############################################
##Title             : intellectron_main.py
##Description       : Main script for domotik project
##Author            : John Bigeon   @ Github
##Date              : 2023073022
##Version           : Early access
##Usage             : MicroPython
##Script_version    : 0.0.1 (not_release)
##Output            :
##Notes             :
###############################################
"""
###############################################
### Package
###############################################
import serial
import re
import os
import time
import datetime
import json
import sys
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
from waveshare_epd import epd2in13_V4
from PIL import Image,ImageDraw,ImageFont
import traceback

###############################################
### Configure the logbook
###############################################
# Configure logging with dynamic log file path
# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create the log directory under the script directory
log_dir = os.path.join(script_dir, "Log")

# Create the log directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Configure the root logger
logging.basicConfig(level=logging.DEBUG)

# Create a file handler for writing to the log file
log_file = os.path.join(log_dir, "logfile_domotik_{0:%Y-%m-%d_%H%M%S}.log".format(datetime.datetime.now()))
file_handler = logging.FileHandler(log_file, mode="w")
file_handler.setLevel(logging.DEBUG)

# Create a stream handler for printing to the terminal
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)

# Define the log message format
formatter = logging.Formatter("%(asctime)s; %(levelname)s; %(message)s")

# Set the formatter for both handlers
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Get the root logger and clear any existing handlers
root_logger = logging.getLogger()
root_logger.handlers.clear()

# Add the handlers to the root logger
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

###############################################
### Configure the InfluxDB connection
###############################################
bucket = "This_is_A_Bucket"
org = "ThisCorp"
token = "This_is_A_Token"
url = "aaa.bb.cc.dd:8086"  # Replace with your InfluxDB 2 URL
url = "http://localhost:8086"

#time.sleep(60) # To be sure that the network is ready
# Connect to the InfluxDB server
client = InfluxDBClient(url=url, token=token)

# MAC address to name mapping dictionary
mac_to_name = {
    'a2:b2:c2:d2:e2:f2': 'Living Room',
    'a3:b3:c3:d3:e3:f3': 'Device 2',
    # Add more mappings as needed
}


###############################################
### JSON checker
###############################################
def is_json(myjson):
    "https://stackoverflow.com/questions/11294535/verify-if-a-string-is-json-in-python"
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def decode_message(msg):
    msg = msg.strip('b').replace('\\', '').strip("'")
    logging.debug(f"Decoded message: {repr(msg)}")
    return msg

def parse_message(msg):
    if not msg or 'not' in msg:
        logging.debug('No message received')
        return None
    if is_json(msg):
        return json.loads(msg)
    else:
        logging.warning('Msg is not a JSON as expected')
        return None

def process_message(parsed_data):
    if parsed_data is not None:
        sender_mac = parsed_data.get("Loc")
        probe_names = parsed_data.get("Prob")
        probe_values = parsed_data.get("Value")
        # You can now use sender_mac, probe_names, and probe_values as needed
        # Additional processing code can go here
        logging.debug(f"Processed message from {sender_mac} with probes {probe_names} and values {probe_values}")
        return True, sender_mac, probe_names, probe_values
    
    else:
        logging.debug("Parsed data is None, skipping processing")
        return False, None, None, None
        
###############################################
### To copy paste infos on the main image
###############################################
def display_sens(img, txt, font, offset):
    # Calculate the size of the second text
    text2_size = font.getbbox(txt)[2], font.getbbox(txt)[3]
    text2_image = Image.new('RGBA', text2_size, (0, 0, 0, 0))  # Mode 'RGBA' for transparency
    
    draw2 = ImageDraw.Draw(text2_image)
    draw2.text((0, 0), txt, font=font, fill=(0, 0, 0, 255))  # Black text
    
    rotated_text2_image = text2_image.rotate(90, expand=1)
    
    img.paste(rotated_text2_image, (image.width - rotated_text2_image.width - offset, 10), rotated_text2_image)  # Adjust the position as needed
 
    
###############################################
### Serial receiver
###############################################
# Connect to the serial port
port = "/dev/ttyACM0"  # Replace with your serial port
baudrate = 115200  # Replace with your baudrate
ser = serial.Serial(port, baudrate, timeout=1.5)

### E-ink display
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create the log directory under the script directory
lib_dir = os.path.join(script_dir, "Lib")

font24 = ImageFont.truetype(os.path.join(lib_dir, 'cambria.ttc'), 24)
font12 = ImageFont.truetype(os.path.join(lib_dir, 'cambria.ttc'), 12)


###############################################
### Main
###############################################
if __name__ == "__main__":
    # Create a write API instance
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Init the display
    epd = epd2in13_V4.EPD()
    logging.info("Display: Init and Clear")
    epd.init()
    epd.Clear(0xFF)

    # read bmp file
    logging.info("Display: Readout of the background")
    image = Image.open(os.path.join(lib_dir, 'wallpaper_domobibiche_eink_v01.bmp'))
    #image = ImageOps.exif_transpose(image)
    logging.info(f"Display: An image with size {image.size}: height={epd.height}, width={epd.width} has been loaded")
    epd.display(epd.getbuffer(image))
    time.sleep(2)
    epd.sleep()
    time.sleep(2)

    try:
        print(21*'#')
        logging.info('Starting the parser')  # Flush the output to the log file immediately
        while True:
            # Read data from the serial port
            msg = ser.readline().decode().strip()
            time_txt = time.strftime('%H:%M:%S')

            decoded_msg = decode_message(msg)
            parsed_data = parse_message(decoded_msg)
            process_done, sender_mac, probe_names, probe_values = process_message(parsed_data)
            
            if process_done:
                # Create a copy of the image to avoid altering the original
                disp_image = image.copy()
                logging.info("Display: Init it")
                epd.init() # wake up the display

                display_sens(disp_image, time_txt, font24, 10)

                # Map MAC address to name
                location = mac_to_name.get(sender_mac, 'Unknown')
                display_sens(disp_image, location, font12, 100)

                # Print the results
                logging.info(f"Sender MAC: {sender_mac}")
                iter_num = 1
                for name, value in zip(probe_names, probe_values):
                    logging.info(f"{name}: {value}")
                    display_sens(disp_image, f"{name}: {value:.2f}", font12, 90-iter_num*12)
                    iter_num += 1

                # Create an InfluxDB data point
                point = Point("Loc").tag("location", sender_mac)
                for name, value in zip(probe_names, probe_values):
                    point.field(name, value)
                    point.tag("location", location)

                # Write the data point to InfluxDB
                try:
                    write_api.write(bucket=bucket, org=org, record=point)
                except:
                    logging.critical('Database: cannot write it')
                
                # # partial update
                logging.debug("Display: Activated")

                epd.displayPartBaseImage(epd.getbuffer(disp_image))
                time.sleep(1.0)
                logging.debug("Display: Sleep mode")
                epd.sleep()
                #logging.info("Display: Clear it")
                #epd.init()
                #epd.Clear(0xFF)

                #time.sleep(1.0)

    except IOError as e:
        logging.error("Display error: %s", str(e))

    except UnicodeDecodeError as decode_error:
        logging.warning("Failed to decode message: %s", decode_error)
        
    except Exception as e:
        logging.error("Exception occurred: %s", str(e))

    except KeyboardInterrupt:
        logging.info("Script execution interrupted by user.")

    #except Exception as e:
        ## Handle exceptions or perform cleanup as needed
        #logging.info("Exception occurred:", str(e))

    finally:
        # Print additional output
        logging.info("Script execution completed.")
        # Close the serial port and disconnect from InfluxDB when done
        ser.close()
        client.close()
        epd2in13_V4.epdconfig.module_exit(cleanup=True)
        print(21*'#')

        # Close the log file
        #log_file.close()


