from flask import Flask, request, jsonify, render_template, send_from_directory, redirect
from flask_socketio import SocketIO
import os
from waitress import serve
from threading import Thread
from datetime import datetime

import paho.mqtt.client as mqtt
import logging

#this server "gets" a request using the JS object "var xhr = new XMLHttpRequest();". Server.py responds with a string within a json object 


logfile_path = '/home/summer1/Desktop/pyenv_try/projects/Keyence_Camera/server_folder/server_logfile.log'
with open(logfile_path, 'w'):
        pass

logging.basicConfig(
    filename=logfile_path,
    level=logging.DEBUG,  # Set the desired log level
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("~"*100)



app = Flask(__name__)
socketio = SocketIO(app)


#these two variable start at the same ammount
mqtt_variable = 0 #holds update
variable = 0 #holds current photo refresh  

photo_file_list = []

#Everyting to do with changing photos
def fetch_photo_list(count, program_number):
    logger.info("FETCHING PHOTOS FROM: /"+program_number)
    #hard set counter for two photos
    #1. find photos dir --> 2. put all photo file names in a list --> 3. sort those files based on time --> 4. then get the top two photos of the sorted list
    #5. return the file locations

    photos_dir = '/home/summer1/Desktop/pyenv_try/projects/Keyence_Camera/server_folder/photos/'+program_number
    logger.debug(str(photos_dir))

    # Check if the 'photos' directory exists, create it if it doesn't
    if not os.path.exists(photos_dir):
        os.makedirs(photos_dir)
        logger.debug("photos dir does not exist, making a new one")

    photo_files = []
    # Iterate over files in the 'photos' directory

    for entry in os.scandir(photos_dir):
        if entry.is_file():
            logger.info(entry.name)
            photo_files.append(entry.name)


    sorted_files = sorted(photo_files, key=lambda x: os.path.getmtime(os.path.join(photos_dir, x)), reverse=True)

    latest_photos = []
    # Iterate over the sorted files and retrieve their timestamps
    for file in sorted_files[:count]:
        timestamp = os.path.getmtime(os.path.join(photos_dir, file))
        timestamp = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        latest_photos.append((file, timestamp))
        logger.info(str(file))
    logger.debug(str(latest_photos))
    return latest_photos#return ((photo_0, timestamp), (photo_1, timstamp))

def fetch_two_photos():
    #fetch one from one folder, and one from antoher

    photo_0 = fetch_photo_list(1, "Program_0")
    photo_1 = fetch_photo_list(1, "Program_1")
    logger.debug("Fetched Two Photos "+ str(photo_0)+" "+str(photo_1))
    photos = [photo_0[0], photo_1[0]]
    return photos

def get_latest_photos():
    #Description: fetch two photos and return a tuple containing (photo, timestamp, program#)
    logger.info("~"*30)
    try:
        logger.info("Get Latest Photos")
        photo_file_list = fetch_two_photos()
        logger.info("Get photo, photo_file_list "+ str(photo_file_list))
        photo_1_file = str(photo_file_list[0][0])
        photo_1_time = str(photo_file_list[0][1])
        photo_2_file = str(photo_file_list[1][0])
        photo_2_time = str(photo_file_list[1][1])

        logger.info("Sending photos now")
        #socketio.emit('get_latest_photos', ((photo_1_file, photo_1_time,"Program_0/"), (photo_2_file, photo_2_time, "Program_1/")))
        return ((photo_1_file, photo_1_time,"Program_0/"), (photo_2_file, photo_2_time, "Program_1/"))#return a tuple of information
    except Exception as e:
        logger.error("Error: " + str(e))

    return 1

def change_mqtt_variable():
    global mqtt_variable
    if mqtt_variable >= 10000: # if 10000 changes made before next refresh (AJAX request), then reset mqtt back to 0
        mqtt_variable = 0
    mqtt_variable += 1

@app.route('/get_variable', methods=['GET'])
def handle_get_variable():
    global mqtt_variable
    logger.debug("handle_get_variable: "+ str(mqtt_variable))
    if mqtt_variable > 0:
        #if a change was made, reset variables. NOTE: mqtt_varaible starts a 0, meaning zero == no change, and anything other than zero is a change
        mqtt_variable = 0
        new_photos_tuple = get_latest_photos()
        if new_photos_tuple == 1:
            logger.error("Tuple not contructed in get_latest_photos")
            return jsonify({'Photos_0':0, 
                        'Photos_1': 0})
        logger.debug("Tuples: "+ str(new_photos_tuple[0]))
        return jsonify({'Photos_0': new_photos_tuple[0], 
                        'Photos_1': new_photos_tuple[1]})
    
    
    
    #must return something (none response) when requested and a change has not been detected
    return jsonify({'Photos_0': 1, 
                        'Photos_1': 1})


@app.route('/photos/<folder>/<path:filename>')
def get_photo(folder, filename):
    return send_from_directory(f'photos/{folder}', filename)
#render page functions
@app.route('/')
def index():
    photo_list = fetch_two_photos()
    return render_template('index.html', photo_0=photo_list[0][0], photo_1=photo_list[1][0])

@app.route('/history')
def history():
    sorted_files_0 = fetch_photo_list(10, "Program_0")#fetch 10 photos from the Program_0 folder
    sorted_files_1 = fetch_photo_list(10, "Program_1")
    logger.debug("program 0: "+ str(sorted_files_0))
    logger.debug("program 1: "+ str(sorted_files_1))
    return render_template('history.html', photos_0=sorted_files_0, photos_1=sorted_files_1)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MQTT broker information
broker = "localhost"
port = 1883
username = "summer1"
password = "PLALUKA5000"
topic = "mqtt/server"

# Callback functions for MQTT

def on_connect(client, userdata, flags, rc):
    logger.info("Connected to MQTT broker with result code: " + str(rc))
    # Subscribe to the topic upon successful connection
    client.subscribe(topic)

def on_message(client, userdata, msg):
    logger.info("~"*30)
    logger.info("Received message: " + str(msg.payload.decode("utf-8")))
    
    # Call get_latest_photos
    logger.info("Getting latest photos")
    change_mqtt_variable()

def on_publish(client, userdata, mid):
    logger.info("Message published")


def on_disconnect(client, userdata, rc):
    logger.info("Disconnected from MQTT broker")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def run_mqtt():

    print("running MQTT client")
    # Create MQTT client instance
    client = mqtt.Client()

    print("Client: "+ str(client))

    # Set callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    # Set username and password if required by the broker
    client.username_pw_set(username, password)

    # Connect to the MQTT broker
    client.connect(broker, port)

    # Start the MQTT loop
    client.loop_start()

    try:
        # Publish a test message
        message = "Hello, MQTT!"
        client.publish(topic, message)

        # Keep the script running
        while True:
            pass

    except KeyboardInterrupt:
        # Disconnect from the MQTT broker
        client.disconnect()
        client.loop_stop()





if __name__ == '__main__':
    update_thread = Thread(target=run_mqtt)
    update_thread.start()


    socketio.run(app, host='0.0.0.0', port=5000)

