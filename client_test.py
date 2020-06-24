import socket
import os

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('localhost', 10000)
print('connecting to {} port {}'.format(*server_address))
sock.connect(server_address)

try:

    # Send data
    print('sending {!r}'.format(0))
    sent = sock.sendto(str(0).encode(), server_address)

    # Receive response
    while True:
        data = sock.recv(4096)
        os.system('cls' if os.name == 'nt' else "printf '\033c'")
        print('received {}'.format(data.decode()))

finally:
    print('closing socket')
    sock.close()
