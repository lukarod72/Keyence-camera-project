For context this project was completed in the summer of 2023. For Magna, Plastcoat as a Comp Eng Student. It's purpose is to both teach me basic computer communication methods (TCP, UDP, MQTT) and solve a real problem they had regarding mis-reading viable Car parts. 
This project includes solving a problem regarding the Keyence IV2 AI camera. It uses a Raspi and the mosquitto Mqtt broker software to 
send triggers and connect a network of different cameras, lighting devices and LED-displays. After photos from the camera are taken, their
information is presented on a local server, and refreshed using AJAX requests. 


This is what the website looks like:
MAIN PAGE (shows the most recent trigger):
![image](https://github.com/lukarod72/Keyence-camera-project/assets/138014461/f62a2320-f399-44e3-b25b-4ef6736e0b5b)

History Page (displays the 10 latest parts):
![image](https://github.com/lukarod72/Keyence-camera-project/assets/138014461/4b34af51-9d86-4e0c-944b-12b1785c1bd7)

