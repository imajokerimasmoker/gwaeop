# RPi Secure Bluetooth Music Controller

This project allows you to securely control a music player on a Raspberry Pi using a Bluetooth connection. It uses Post-Quantum Cryptography (PQC) to sign commands, ensuring that only an authorized client can control the music player.

## Features

-   Control your music player remotely over Bluetooth.
-   **Secure command authentication** using PQC signatures (Dilithium).
-   Simple command-based protocol.

## Requirements

-   A Raspberry Pi with Bluetooth enabled.
-   Python 3.
-   `mpv` media player installed on the Raspberry Pi.
-   A second device with Bluetooth to act as the client.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd rpi-secure-bluetooth-music-controller
    ```

2.  **Install dependencies:**
    On both the Raspberry Pi (server) and the client device, install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```
    You may also need to install system-level Bluetooth and build dependencies. On Debian-based systems (like Raspberry Pi OS), you can do this with:
    ```bash
    sudo apt-get update
    sudo apt-get install bluetooth libbluetooth-dev build-essential
    ```

3.  **Install mpv:**
    On your Raspberry Pi, install `mpv`. The command depends on your Linux distribution.

    -   For **Debian-based systems** (like Raspberry Pi OS):
        ```bash
        sudo apt-get install mpv
        ```
    -   For **Fedora:**
        ```bash
        sudo dnf install mpv
        ```

4.  **Generate PQC Keys:**
    Run the key generation script to create a public and private key pair.
    ```bash
    python3 generate_keys.py
    ```
    This will create `public_key.key` and `private_key.key`.

5.  **Distribute Keys:**
    -   Copy the `public_key.key` to the Raspberry Pi (server).
    -   Copy the `private_key.key` to the client device.
    -   **Important:** Keep the `private_key.key` secure and do not share it.

6.  **Pair your devices:**
    Pair your Raspberry Pi with your client device using your OS's standard Bluetooth pairing process.

## Usage

1.  **Run the server on the Raspberry Pi:**
    ```bash
    python3 server/server.py
    ```

2.  **Run the client on your control device:**
    Find the Bluetooth address of your Raspberry Pi (e.g., with `bluetoothctl scan on`), then run the client:
    ```bash
    python3 client/client.py <rpi-bluetooth-address>
    ```

3.  **Send commands:**
    Once connected, you can type commands like `play`, `pause`, `next`, etc. The client will automatically sign the commands before sending them. You can also load a file for playback with `load /path/to/media.mp3`.
