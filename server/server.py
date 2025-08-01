import subprocess
import json
import oqs
from bluetooth import (
    BluetoothSocket,
    RFCOMM,
    PORT_ANY,
    advertise_service,
    SERIAL_PORT_CLASS,
    SERIAL_PORT_PROFILE,
)

# Service UUID and PQC Algorithm must match the client
UUID = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
SIG_ALGORITHM = "Dilithium2"
PUBLIC_KEY_FILE = "public_key.key"

def load_public_key():
    """Loads the PQC public key from a file."""
    try:
        with open(PUBLIC_KEY_FILE, "rb") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Public key file not found at '{PUBLIC_KEY_FILE}'")
        print("Please generate keys and place the public key in the same directory as the server script.")
        return None

def run_command(command):
    """Executes a command using mpc."""
    try:
        allowed_commands = ["play", "pause", "stop", "next", "prev", "volume"]
        cmd_part = command.split(" ")[0]

        if cmd_part not in allowed_commands:
            return f"Command not allowed: {command}"

        full_command = f"mpc {command}"
        print(f"Executing: {full_command}")
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def start_server(public_key):
    """Starts the Bluetooth server and listens for signed commands."""
    server_sock = BluetoothSocket(RFCOMM)
    server_sock.bind(("", PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    advertise_service(
        server_sock, "RPiSecureMusicPlayer", service_id=UUID,
        service_classes=[UUID, SERIAL_PORT_CLASS], profiles=[SERIAL_PORT_PROFILE]
    )
    print(f"Waiting for connection on RFCOMM channel {port}")

    sig = oqs.Signature(SIG_ALGORITHM)

    try:
        while True:
            client_sock, client_info = server_sock.accept()
            print(f"Accepted connection from {client_info}")
            try:
                while True:
                    data = client_sock.recv(1024)
                    if not data:
                        break

                    try:
                        message = json.loads(data.decode("utf-8"))
                        command = message["command"]
                        signature = bytes.fromhex(message["signature"])

                        print(f"Received command: '{command}'")

                        is_valid = sig.verify(command.encode('utf-8'), signature, public_key)

                        if is_valid:
                            print("Signature is valid.")
                            response = run_command(command)
                            client_sock.send(response.encode("utf-8"))
                        else:
                            print("Signature is invalid! Rejecting command.")
                            client_sock.send("Invalid signature.".encode("utf-8"))

                    except (json.JSONDecodeError, KeyError):
                        print("Received invalid message format.")
                        client_sock.send("Invalid message format.".encode("utf-8"))

            except IOError:
                print("Connection lost.")
            finally:
                print("Closing client socket.")
                client_sock.close()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_sock.close()
        print("Server socket closed.")

if __name__ == "__main__":
    public_key = load_public_key()
    if public_key:
        start_server(public_key)
    else:
        print("Server cannot start without a public key.")
