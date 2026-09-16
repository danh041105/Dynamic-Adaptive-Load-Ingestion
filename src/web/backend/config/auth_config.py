import os
from dotenv import load_dotenv

load_dotenv()

class AuthConfig:

    @staticmethod
    def get_secret_key() -> str:
        secret_key = os.getenv("SECRET_KEY")
        return secret_key

    @staticmethod
    def get_algorithm() -> str:
        algorithm = os.getenv("ALGORITHM")
        return algorithm

    @staticmethod
    def get_access_token_expire_minutes() -> int:
        access_token_expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        return int(access_token_expire_minutes)