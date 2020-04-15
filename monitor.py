from twilio.rest import Client
import paho.mqtt.client as mqtt
import json
import time
from restart_service import ssh_restart
import smtplib 

ssh_restart = ssh_restart()

account_sid = "AC07bdafbca4a084659d86bd7110625b41"
auth_token = "d3408e409d42a4dd60d7de20f7d81c3b"
twilio_client = Client(account_sid, auth_token)

server_address = "192.168.0.10"

topics = "status/sensor/#"

critical_service_list = ['lounge','master','heater_controls','heater_relay','heater_backend']
critical_services = {
    'lounge':{'status':'online','attempts':0,
        'ip':'192.168.0.70','service':'mi_temp_reader_lounge.service'},

    'master':{'status':'online','attempts':0,
        'ip':'192.168.0.75','service':'mi_temp_reader_master.service'},

    'heater_controls':{'location':'heater_controls','status':'online','attempts':0,
        'ip':'','service':''},

    'heater_relay':{'status':'online','attempts':0,
        'ip':'192.168.0.81','service':'heater.service'},

    'heater_backend':{'status':'online','attempts':0,
        'ip':'','service':''}
}

def send_email(location, status):
    text = 'Your ' + str(location) + ' is ' + str(status)
    subject = "heater offline"
    sender = "central.heater@gmail.com"
    pwd = "3AO40eMJE423"
    recipient = "davideo.ezy@gmail.com"
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (sender, ", ".join(recipient), subject, text)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(sender, pwd)
    server.sendmail(sender, recipient, message)
    server.close()



def send_message(location, status):
    msg = 'Your ' + str(location) + ' code is ' + str(status)
    message = twilio_client.messages.create(body=msg, from_='whatsapp:+14155238886',to='whatsapp:+61410445123')

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topics,0)

def on_disconnect(client, userdata, rc):
    print('disconnected')
    client.connect(server_address, keepalive=60)
    print('connected')

def on_message(client, userdata, msg):
    global critical_services
    global mqtt_client
    data = str(msg.payload.decode("utf-8"))
    jsonData=json.loads(data)    
    if jsonData['location'] in critical_service_list:
        print('service identified')
        critical_services[jsonData['location']]['status'] = jsonData['status']
        if jsonData['status'] == 'online':
            critical_services[jsonData['location']]['attempts'] = 0
            print('service online')
        elif jsonData['status'] == 'offline':
            print('service offline')
            mqtt_client.disconnect()
            print('mqtt disconnected, attempt ' + str(critical_services[jsonData['location']]['attempts'] ))
            if critical_services[jsonData['location']]['ip'] != '':
                print('restartable service')
                if critical_services[jsonData['location']]['attempts'] == 1:
                    try:
                        print('restarting service')
                        ssh_restart.remote_service_command(
                            critical_services[jsonData['location']]['ip'], 
                            'restart_service', 
                            critical_services[jsonData['location']]['service']
                            )
                        print('service restarted')
                    except Exception:
                        print('failed service restart')
                        pass
                elif critical_services[jsonData['location']]['attempts'] == 2:
                    print('try restarting device')
                    try:
                        ssh_restart.remote_service_command(
                            critical_services[jsonData['location']]['ip'],
                            'restart_device',
                            critical_services[jsonData['location']]['service']
                            )
                        print('device restarted')
                    except Exception:
                        print('failed device restart')
                        pass
            if critical_services[jsonData['location']]['attempts'] == 3:
                print('sending message')
                try:
                    send_message(jsonData['location'], jsonData['status'])
                    print('message sent')
                except Exception: 
                    print('failed sending message')
                    pass
            if critical_services[jsonData['location']]['attempts'] == 4:
                try:
                    send_email(jsonData['location'], jsonData['status'])
                except Exception:
                    pass
            
            print('incrementing counter')        
            critical_services[jsonData['location']]['attempts'] += 1
            print('incremented to attempts = ' + str(critical_services[jsonData['location']]['attempts']) + '. Sleeping')
            time.sleep(90)
            print('awake')

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect

mqtt_client.connect(server_address, keepalive=120)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
mqtt_client.loop_forever()

