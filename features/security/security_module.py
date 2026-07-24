# security_module.py

import os
from cryptography.fernet import Fernet

class SecurityModule:
    """Handles secure encryption/decryption of administrative credentials."""
    
    KEY_FILE = "data/secret.key"

    def __init__(self):
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self):
        if not os.path.exists(self.KEY_FILE):
            key = Fernet.generate_key()
            with open(self.KEY_FILE, "wb") as key_file:
                key_file.write(key)
            return key
        with open(self.KEY_FILE, "rb") as key_file:
            return key_file.read()

    def encrypt_data(self, plaintext: str) -> str:
        """Encrypts a string and returns a utf-8 encoded string."""
        token = self.cipher.encrypt(plaintext.encode())
        return token.decode()

    def decrypt_data(self, encrypted_text: str) -> str:
        """Decrypts an encrypted string and returns the plaintext."""
        token = self.cipher.decrypt(encrypted_text.encode())
        return token.decode()