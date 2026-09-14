from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt

from .config import get_required_env


SECRET_KEY = get_required_env("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_BCRYPT_MAX_PASSWORD_BYTES = 72


def _password_bytes(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > _BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Пароль не може перевищувати 72 байти для bcrypt.")
    return password_bytes

# Функція перевірки пароля (чи співпадає введений з тим, що в базі)
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Безпечно звірити пароль лише з bcrypt-хешем."""
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), password_hash.encode("utf-8"))
    except (TypeError, ValueError):
        return False

# Функція для створення хешу (для реєстрації)
def get_password_hash(password: str) -> str:
    """Створити bcrypt-хеш без збереження відкритого пароля."""
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")

# Функція створення токена доступу (JWT)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    # if expires_delta:
    #     expire = datetime.utcnow() + expires_delta
    # else:
    #     expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Використовуємо datetime.now(timezone.utc) замість utcnow()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Додаємо час "смерті" токена
    to_encode.update({"exp": expire})
    
    # Кодуємо в рядок
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
