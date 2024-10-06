import json
import subprocess
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)



wifi_disconnected = False

# Function to connect to WiFi using nmcli
def connect_to_wifi(ssid, password):
    try:
        # Add and activate the WiFi connection
        subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
            'password', password
        ], check=True)
        logging.info(f"Connected to WiFi network '{ssid}'")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to connect to WiFi network '{ssid}': {e}")

# Function to ping Google to check connectivity
def check_wifi():
    response = subprocess.run(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return response.returncode == 0

# Function to restart the service
def restart_service(service_name):
    logging.info(f"Restarting service: {service_name}...")
    subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=True)
    subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True)

# Function to stop the service
def disable_service(service_name):
    logging.info(f"Disabling service: {service_name}...")
    subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=True)
    subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=True)

# Initial WiFi connection attempt
if check_wifi():
    logging.info("WiFi is connected....")
else:
    logging.error("WiFi not connected. Attempting to reconnect...")
    # Read credentials from the text file
    with open('credentials.txt', 'r') as file:
        data = json.load(file)

    wifi_ssid = data['ssid']
    wifi_password = data['password']
    connect_to_wifi(wifi_ssid, wifi_password)
    time.sleep(5)  # Wait a bit before retrying
    if check_wifi():
        logging.info("Wifi connected")
    else:
        logging.error("Unable to connect to WiFi after restarting service. Exiting.")

# Time interval for WiFi check
wifi_check_interval = 30
last_wifi_check = time.time()

# Main loop
while True:
    current_time = time.time()
    
    # Check WiFi status periodically
    if current_time - last_wifi_check >= wifi_check_interval:
        if not check_wifi():
            if not wifi_disconnected:
                logging.info("WiFi not connected, restarting service...")
                restart_service("hostapd")
                restart_service("access-point-server")
                wifi_disconnected = True
            else:
                logging.info("Waiting connection...")
                # Read credentials from the text file
                with open('credentials.txt', 'r') as file:
                    data = json.load(file)
                wifi_ssid = data['ssid']
                wifi_password = data['password']
                connect_to_wifi(wifi_ssid, wifi_password)
            time.sleep(5)  # Wait a bit before retrying
            if check_wifi():
                disable_service("hostapd")
                disable_service("access-point-server")
                restart_service("wpa_supplicant.service")
                restart_service("dhspcd.service")
                wifi_disconnected = False
        # Update the last WiFi check time
        last_wifi_check = current_time
    # Sleep briefly to yield control back to the MQTT loop
    time.sleep(1)
