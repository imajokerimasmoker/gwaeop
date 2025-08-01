import sys
import json
import oqs
from bluetooth import (
    BluetoothSocket,
    RFCOMM,
    find_service,
)

# Service UUID and PQC Algorithm must match the server's
UUID = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
SIG_ALGORITHM = "Dilithium2"
PRIVATE_KEY_FILE = "private_key.key"

def load_private_key():
    """Loads the PQC private key from a file."""
    try:
        with open(PRIVATE_KEY_FILE, "rb") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Private key file not found at '{PRIVATE_KEY_FILE}'")
        print("Please generate keys and place the private key in the same directory as the client script.")
        return None

def find_rpi_service(addr):
    """Finds the RPi Music Player service on a given address."""
    print(f"Searching for RPi Secure Music Player service on {addr}...")
    service_matches = find_service(uuid=UUID, address=addr)

    if not service_matches:
        print("Couldn't find the service.")
        return None

    match = service_matches[0]
    return match["port"], match["host"]

def start_client(addr, private_key):
    """Starts the Bluetooth client and sends signed commands."""
    port_host = find_rpi_service(addr)
    if not port_host:
        return

    port, host = port_host
    sock = BluetoothSocket(RFCOMM)
    sig = oqs.Signature(SIG_ALGORITHM)

    try:
        print(f"Connecting to {host} on port {port}...")
        sock.connect((host, port))
        print("Connected successfully.")

        while True:
            command = input("Enter command (e.g., play, pause, exit): ")
            if not command:
                continue

            # Sign the command
            signature = sig.sign(command.encode('utf-8'), private_key)

            # Prepare message
            message = {
                "command": command,
                "signature": signature.hex() # Convert bytes to hex for JSON serialization
            }

            sock.send(json.dumps(message))

            if command.lower().strip() == "exit":
                break

            response = sock.recv(1024)
            print(f"Server response: {response.decode('utf-8')}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing socket.")
        sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <server-bt-address>")
        sys.exit(1)

    server_address = sys.argv[1]
    private_key = load_private_key()

    if private_key:
        start_client(server_address, private_key)
    else:
        print("Client cannot start without a private key.")
