import os
import subprocess
import socket
import time

# Define the SSID and password for the access point
ssid = "Raspberry Pi AP"
password = "raspberry"

# Check if already connected to WiFi
def is_connected():
    try:
        # Check if wlan0 has an IP address
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ip = result.stdout.strip()
        return bool(ip)
    except Exception as e:
        print(f"Error checking connection: {e}")
        return False

# Create a virtual network interface for the access point
os.system("sudo iw dev wlan0 interface add ap0 type __ap")

# Configure the IP address and netmask for the access point interface
os.system("sudo ip addr add 192.168.4.1/24 dev ap0")

# Enable the access point interface
os.system("sudo ip link set ap0 up")

# Create a hostapd configuration file with the SSID and password
with open("/etc/hostapd/hostapd.conf", "w") as f:
    f.write(f"""
interface=ap0
ssid={ssid}
wpa_passphrase={password}
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP""")

# Start the hostapd service with the configuration file
os.system("sudo hostapd -B /etc/hostapd/hostapd.conf")

# Start the dnsmasq service to provide DHCP and DNS services
os.system("sudo dnsmasq -C /dev/null -kd -F 192.168.4.2,192.168.4.20 -i ap0 --bind-dynamic")

# Enable IP forwarding to allow internet access for the connected devices
os.system("sudo sysctl net.ipv4.ip_forward=1")

# Configure NAT to forward packets from the access point interface to the internet interface (eth0)
os.system("sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")

# Define the captive portal web page content with SSID and password fields
html = """
<title>Raspberry Pi Captive Portal</title>
<h1>Welcome to Raspberry Pi Captive Portal</h1>
<p>You are now connected to your Raspberry Pi as WiFi Access Point</p>
<p>Please enter your WiFi credentials and email address to connect to the internet.</p>
<form action="/login" method="post">
SSID: <input type="text" name="ssid"><br>
Password: <input type="password" name="password"><br>
Email: <input type="email" name="email"><br>
<input type="submit" value="Login">
</form>
"""

# Create a socket object to listen for HTTP requests on port 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 80))
s.listen(5)

def connect_wifi(ssid, wifi_password):
    try:
        # Use nmcli to connect to WiFi
        command = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', wifi_password]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Successfully connected to {ssid}")
            return True
        else:
            print(f"Failed to connect: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error connecting to WiFi: {e}")
        return False

# Loop to handle HTTP requests
while True:
    if not is_connected():
        # Accept a connection from a client
        conn, addr = s.accept()
        print(f"Connection from {addr}")
        
        # Receive the HTTP request from the client
        request = conn.recv(1024).decode()
        print(f"Request: {request}")
        
        # Parse the request line to get the method and path
        request_line = request.split("\n")[0]
        method, path, version = request_line.split()
        
        # If the path is /login, extract the WiFi credentials and email from the request body
        if path == "/login" and method == "POST":
            try:
                # Get the request body by splitting on an empty line
                body = request.split("\r\n\r\n")[1]
                # Split the body on "&" to get the parameters
                params = body.split("&")
                ssid = params[0].split("=")[1]
                wifi_password = params[1].split("=")[1]
                email = params[2].split("=")[1]
                
                # Save the email to a file
                with open("email.txt", "w") as f:
                    f.write(f"Email: {email}\n")
                
                # Attempt to connect to the WiFi network
                if connect_wifi(ssid, wifi_password):
                    # If connected, stop the captive portal
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Connected to WiFi!</h1>"
                    conn.send(response.encode())
                    print("Connected to WiFi. Stopping captive portal.")
                    break
                else:
                    # If connection fails, return an error page
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Failed to connect to WiFi. Please try again.</h1>"
                    conn.send(response.encode())
            except Exception as e:
                print(f"Error processing login: {e}")
        else:
            # Send the captive portal web page
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
            conn.send(response.encode())
        
        # Close the connection with the client
        conn.close()
    else:
        print("Already connected to WiFi. Exiting captive portal.")
        break

# Stop the access point and services when done
os.system("sudo ip link set ap0 down")
os.system("sudo iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE")
os.system("sudo systemctl stop hostapd")
os.system("sudo systemctl stop dnsmasq")
