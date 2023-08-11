import paho.mqtt.client as mqtt
import socket
import time

import os
from ftplib import FTP
import logging

# Reset the log for debug and entry
logfile_path = '/home/summer1/Desktop/pyenv_try/projects/Keyence_Camera/camera_logfile.log'
with open(logfile_path, 'w'):
        pass


# Configure the logging settings
logging.basicConfig(
    filename=logfile_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Create a logger instance
logger = logging.getLogger(__name__)

logger.info("~"*100)

#to start from boot do this:
#1. Go to /etc/init.d/pyenv_startup.sh
#2. add script

#import move_folder

#Purpose: write a script that can trigger the IV2 Keyence AI camera and recieve a status and a photo

#step 1 : send a trigger to the camera
#step 2 : recieve a status from the camera
#step 3 : recieve a photo from FTP, and display on a website hosted on the raspi

class connect_TCP:

    def __init__(self, ip, port):
        self.ip_address = ip
        self.port = port

    def converting_hex(self, command_string):
        logger.info("\nConverting>>>>")
        hex_command = command_string.encode().hex()
        command_bytes = bytes.fromhex(hex_command)
        return command_bytes

    def connecting_and_sending(self, command_bytes, sock):
        logger.info("Connecting>>>>" + self.ip_address)
        sock.connect((self.ip_address, self.port))
        logger.info("Connected>>>>")
        logger.info("Sending>>>>")
        sock.sendall(command_bytes)

    def send_command_string_single(self, command_string):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        response = ''
        try:
            command_bytes = self.converting_hex(command_string)
            self.connecting_and_sending(command_bytes, sock)
            if command_string == 'LOFF\r':
                return response
            response = str(sock.recv(512).decode())
        except socket.error as e:
            logger.error("\nSocket error: " + str(e))
            logger.info("Try Re-connecting")
            time.sleep(1.5)
            self.send_command_string_single(command_string)
        except Exception as e:
            logger.error("\nError: " + str(e))
        finally:
            sock.close()
        logger.info("~" * 15)
        return str(response)

    def send_command_string_multiple(self, command_string):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        response = []
        try:
            command_bytes = self.converting_hex(command_string)
            self.connecting_and_sending(command_bytes, sock)
            if command_string == 'LOFF\r':
                return response
            response.append(str(sock.recv(512).decode()))
            time.sleep(0.5)
            response.append(str(sock.recv(512).decode()))
        except socket.error as e:
            logger.error("\nSocket error: " + str(e))
            logger.info("Try Re-connecting")
            time.sleep(1.5)
            self.send_command_string_multiple(command_string)
        except Exception as e:
            logger.error("\nError: " + str(e))
        finally:
            sock.close()
        logger.info("~" * 15)
        return response
    




#DEFINE classes and clients here
Barcode = connect_TCP('192.168.0.205', 8600)
Camera = connect_TCP("192.168.0.203", 8500)


Barcodes = {
    1: "QR-Code",
    2: "2D-Barcode", 
    
    3: "PDF417", 
    5: "GS1 DataBar(RSS)",
    6: "1D-Barcode", 

    7: "ITF", 
    8: "2ofS", 
    9: "NW-7(Codebar)", 
    10: "UPC/EAN/JAN", 
    11: "GS1-128(CODE128)", 
    12: "COOP2of5", 
    13: "CODE93", 
    14: "CC-A/B(GS1 DataBar)", 
    15: "CC-A/B(EAN/UPC)",
    16: "CC-A/B/C(GS1-128)", 
    18: "Pharmacode"
}



#task code - used for exucutions
def run_scanner():

    print("Scanner: Reading - ON")
    global Barcode
    response_SR = Barcode.send_command_string_multiple('LON\r')
    response_SR = sorted(response_SR, key=lambda x: x[0])# this is a sorted list
    print("Scanner: Reading - OFF")
    time.sleep(0.5)
    Barcode.send_command_string_single('LOFF\r')

    # response_SR[0] = response_SR[0].rstrip('\r\n')
    # response_SR[1] = response_SR[1].rstrip('\r\n')

    for i in range(len(response_SR)):
        response_SR[i] = response_SR[i].rstrip('\r\n')  # get rid of all carriage returns and new lines
        temp = response_SR[i].split(":")  # split the two sides - temp will have two elements
        temp[0] = Barcodes[int(temp[0])]  # edit the barcode Symbology
        response_SR[i] = ":".join(temp)  # join back the list
        logger.debug(str(response_SR[i]))



    print("Barcode Response: "+ str(response_SR))
    logger.debug(response_SR[0] + "||" + response_SR[1])

    return (response_SR[0] + "," + response_SR[1]) # 2:123123/6:123123 - NOTE: these are what the barcode data looks like


# Transfer from ftpuser1 to summer1
def transfer_photos_from_FTP(keyword, barcode_data):
    logger.info("Transfer from FTP: Starting")
    # FTP server credentials
    server_address = 'localhost'
    username = 'ftpuser1'
    password = 'PASSWORD'#change to your ftp credentials

    # Destination folder for transferred photos
    destination_folder = '/home/summer1/Desktop/pyenv_try/projects/Keyence_Camera/server_folder/photos/'+keyword

    # Connect to the FTP server
    ftp = FTP(server_address)
    ftp.login(username, password)

    # Change to the appropriate directory on the FTP server
    ftp.cwd('/home/Camera_photos')

    # List files on the FTP server
    files = ftp.nlst()

    # Sort files based on modification time
    files.sort(key=lambda file: ftp.sendcmd('MDTM ' + file)[4:], reverse=True)

    if len(files) > 0:
        # Get the latest modified file
        latest_file = files[0]

        # Generate a new name for the transferred file with the keyword
        base_name, file_extension = os.path.splitext(latest_file)
        photo_ID = base_name.split('_')[1]#seperate the base_name based on underscored. Example: "Photo_0008" --> ["Photo", '0008']
        new_file_name = f"Barcode:({barcode_data})-{keyword}{file_extension}" #NOTE: PHOTO Tag INCLUDES --> ID:xxxx-Program_xx

        # Transfer the file to the destination folder with the new name. Write latest_file onto teh local_file (take the original file name and write it into a new file name 
        # locally)
        local_filename = os.path.join(destination_folder, new_file_name)
        with open(local_filename, 'wb') as local_file:
            ftp.retrbinary('RETR ' + latest_file, local_file.write)

        logger.info(f'Latest photo "{latest_file}" transferred to "{new_file_name}" successfully.')
    else:
        logger.info('No photos found on the FTP server.')

    # Close the FTP connection
    ftp.quit()

    logger.info('Photos transferred successfully.')



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MQTT broker information
broker = "localhost"
port = 1883
username = "summer1"
password = "PLALUKA5000"
camera_topic = "mqtt/camera"
server_topic = "mqtt/server"
display_topic = "mqtt/LED_display"

programs = {
    0: '(Blue Clip One)',
    1: '(Blue Clip Two)'
}
photo_files = {
    0: 'Program_0',
    1: 'Program_1'
}


def perform_pre_connect_actions(client):
    client.username_pw_set(username, password)
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(camera_topic)

    client.publish(camera_topic, "STARTING")
# The callback for when a PUBLISH message is received from the server.

def camera_trigger(clip_type, scanner_response):
    logger.info("Camera: Triggering, "+"Program: "+programs[clip_type])
    response = Camera.send_command_string_single("T2\r")

    temp_array = response.split(',') #note.split is a method belonging to the string class


    logger.info('CAMERA Reponse: '+ temp_array[0]+ ' '+ temp_array[2])    

    #NOW get photo from FTP server -- HERE
    logger.info("Waiting for File transfer from camera before FTP")
    time.sleep(1.0)#WAIT FOR new photo to be trasnfered
    transfer_photos_from_FTP(photo_files[clip_type], scanner_response)#NOTE: THIS HAS TO BE THE FILE PATH AS WELL
    return temp_array[2]

def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    global Camera

    logger.info("~"*50)
    

    #check for warning message that prevent reading

    #trigger and response command
    if(msg.payload == b'Trigger'):

        Read_program_response = Camera.send_command_string_single('PR\r')
        #take carrage return off the end of the response
        Read_program_response = Read_program_response.rstrip('\r')
        clip_type = int(Read_program_response.split(',')[1])

        scanner_response = run_scanner()#get barcode data
        

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Camera TRIGGER 1
        camera_response = camera_trigger(clip_type, scanner_response)
        time.sleep(0.2)
        #change clip type
        org_clip = clip_type
        clip_type = clip_type - 1 if clip_type > 0 else clip_type + 1

        #Switch to other program
        Camera.send_command_string_single(f"PW,00{clip_type}\r")
        logger.debug("Clip Type: "+ str(clip_type))

        #Camera TRIGGER 2
        if camera_trigger(clip_type, scanner_response) == 'NG':
            #if camera trigger is NG, then no matter what the first trigger was, the part is NG
            camera_response = 'NG'    
        print(camera_response)


        #Switch back to first program
        Camera.send_command_string_single(f"PW,00{org_clip}\r")
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


        client.publish(display_topic, camera_response)
        logger.info("Wait to send refresh...")
        client.publish(server_topic, "refresh")

    logger.info("~"*30)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == '__main__':
    # MQTT client setup
    client = mqtt.Client()
    client.on_connect = on_connect
    perform_pre_connect_actions(client)
    client.on_message = on_message
    client.connect(broker, port, 60)

    # Blocking call that processes network traffic, dispatches callbacks, and handles reconnecting.
    client.loop_forever()


logger.info("~"*100)