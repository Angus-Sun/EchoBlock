import socket
from gpiozero import LED

# Define LED pins
leds = {
    "LED1": LED(7),
    "LED2": LED(8),
    "LED3": LED(25),
    "LED4": LED(24),
    "LED5": LED(23)
}

HOST = "0.0.0.0"  
PORT = 12345  

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print("Server is listening for commands...")

while True:
    client_socket, addr = server_socket.accept()
    print(f"Connected to {addr}")

    while True:
        data = client_socket.recv(1024).decode()
        if not data:
            break  

        command, state = data.split(":")  
        print(f"Received command: {command} -> {state}")

        if command in leds:
            if state == "ON":
                leds[command].on()
            elif state == "OFF":
                leds[command].off()

    client_socket.close()