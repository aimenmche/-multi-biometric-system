import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT = os.getenv("ENCRYPTION_SALT", "biometric-system-salt-value").encode()
MASTER_KEY = os.getenv("MASTER_KEY", "master-key-biometric-system-2024")


def _derive_key() -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(MASTER_KEY.encode()))
    return key


def encrypt_biometric_template(template_data: str) -> str:
    key = _derive_key()
    f = Fernet(key)
    encrypted = f.encrypt(template_data.encode())
    return encrypted.decode()


def decrypt_biometric_template(encrypted_data: str) -> str:
    key = _derive_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data.encode())
    return decrypted.decode()
