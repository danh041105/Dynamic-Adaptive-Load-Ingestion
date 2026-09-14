import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

def get_nifi_url()-> str:
    nifi_url = os.getenv("nifi_url")
    return nifi_url

def get_nifi_parameter_token() -> Dict[str, str]: 
    nifi_username = os.getenv("nifi_username")
    nifi_password = os.getenv("nifi_password")
    return dict(username=nifi_username, password=nifi_password)

def get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")
    return secret_key

def get_algorithm() -> str:
    algorithm = os.getenv("ALGORITHM")
    return algorithm

def get_access_token_expire_minutes() -> int:
    access_token_expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    return int(access_token_expire_minutes)