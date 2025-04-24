from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
import os
from passlib.hash import django_pbkdf2_sha256, django_bcrypt, django_argon2, django_des_crypt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
COOKIE_NAME = "access_token"

def create_jwt(data: dict, expires_delta: timedelta = timedelta(hours=2)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str):
    from jose import JWTError
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def hash_password(password: str):
    return django_pbkdf2_sha256.hash(password)

def verify_password(password: str, hashed_password: str):
    return django_pbkdf2_sha256.verify(password, hashed_password)
