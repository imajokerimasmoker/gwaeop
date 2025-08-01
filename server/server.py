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

import socket
import tempfile
import os

MPV_SOCKET_PATH = os.path.join(tempfile.gettempdir(), "mpv_socket")

def send_mpv_command(command_obj):
    """Sends a command to the mpv IPC socket."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(MPV_SOCKET_PATH)
            s.sendall(json.dumps(command_obj).encode('utf-8') + b'\n')
            response = s.recv(1024)
            return json.loads(response.decode('utf-8'))
    except Exception as e:
        print(f"Error communicating with mpv: {e}")
        return {"error": str(e)}

def run_command(command):
    """Executes a command using mpv."""
    parts = command.split(" ", 1)
    cmd = parts[0]

    command_map = {
        "play": ["set_property", "pause", False],
        "pause": ["set_property", "pause", True],
        "stop": ["stop"],
        "next": ["playlist-next"],
        "prev": ["playlist-prev"],
    }

    if cmd in command_map:
        response = send_mpv_command({"command": command_map[cmd]})
    elif cmd == "volume" and len(parts) > 1:
        try:
            level = int(parts[1])
            response = send_mpv_command({"command": ["set_property", "volume", level]})
        except (ValueError, IndexError):
            response = {"error": "Invalid volume level"}
    elif cmd == "load" and len(parts) > 1:
        response = send_mpv_command({"command": ["loadfile", parts[1]]})
    else:
        response = {"error": "Unknown command"}

    return json.dumps(response)


def start_server(public_key):
    """Starts the Bluetooth server and listens for signed commands."""
    # Start mpv in the background
    subprocess.Popen(
        ["mpv", "--idle", f"--input-ipc-server={MPV_SOCKET_PATH}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"mpv started with IPC socket at {MPV_SOCKET_PATH}")

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
