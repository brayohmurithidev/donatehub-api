from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


FERNET_KEY = settings.ENCRYPTION_SECRET_KEY
fernet = Fernet(FERNET_KEY)


def encrypt_secret(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    decoded = fernet.decrypt(value.encode()).decode()
    print("from decrypt -> decoded : ", decoded)
    return decoded


