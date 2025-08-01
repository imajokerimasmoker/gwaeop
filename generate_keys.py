import oqs
import os

# The PQC signature algorithm to use
SIG_ALGORITHM = "Dilithium2"

def generate_keys():
    """Generates a PQC key pair and saves them to files."""

    # Ensure the chosen algorithm is supported by the OQS library
    try:
        sig = oqs.Signature(SIG_ALGORITHM)
    except oqs.MechanismNotSupportedError:
        print(f"Error: The signature algorithm '{SIG_ALGORITHM}' is not supported by this build of liboqs.")
        print("Supported signature algorithms are:", ", ".join(oqs.get_enabled_sigs()))
        return

    print(f"Generating key pair for {SIG_ALGORITHM}...")

    # Generate the key pair
    public_key = sig.generate_keypair()
    private_key = sig.export_secret_key()

    # Define file paths
    pub_key_file = "public_key.key"
    priv_key_file = "private_key.key"

    # Save the public key
    with open(pub_key_file, "wb") as f:
        f.write(public_key)
    print(f"Public key saved to {pub_key_file}")

    # Save the private key
    with open(priv_key_file, "wb") as f:
        f.write(private_key)
    print(f"Private key saved to {priv_key_file}")

    # Add a reminder about keeping the private key safe
    print("\nIMPORTANT: Keep your private_key.key file secure and do not share it.")
    print("The public_key.key should be placed on the server (Raspberry Pi).")
    print("The private_key.key should be placed on the client device.")


if __name__ == "__main__":
    generate_keys()
