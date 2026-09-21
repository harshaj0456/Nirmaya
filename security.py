"""
Encryption-at-rest demonstration.

The problem statement requires encryption and CERT-In/ISO 27001-aligned
hosting. We can't stand up real cloud infrastructure inside a hackathon
prototype, but we CAN demonstrate the actual mechanism a production system
would use for one genuinely sensitive field: subject-identifying names.

Fernet is symmetric authenticated encryption (AES128 + HMAC under the
hood). In production the key would come from a managed KMS (e.g. AWS KMS
in the data-resident ap-south-1 region), never a hardcoded constant - the
comment below flags that explicitly so nobody mistakes this for
production-ready key management.
"""
from cryptography.fernet import Fernet

# DEMO ONLY: a real deployment must pull this from a KMS/secrets manager,
# scoped to data-resident infrastructure, never from source code.
_KEY = Fernet.generate_key()
_FERNET = Fernet(_KEY)


def encrypt(value: str) -> str:
    return _FERNET.encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _FERNET.decrypt(token.encode()).decode()


def mask(value: str) -> str:
    """What a role without decrypt permission sees instead of plaintext."""
    return "•" * max(len(value), 4)
