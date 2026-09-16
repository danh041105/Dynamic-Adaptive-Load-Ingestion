import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

class NifiConfig:
    @staticmethod
    def get_nifi_url()-> str:
        nifi_url = os.getenv("nifi_url")
        if not nifi_url:
            raise RuntimeError("NIFI_URL chưa được cấu hình")
        return nifi_url

    @staticmethod
    def get_nifi_login_payload() -> Dict[str, str]: 
        nifi_username = os.getenv("nifi_username")
        nifi_password = os.getenv("nifi_password")

        if not nifi_username or not nifi_password:
            raise RuntimeError("NIFI_USERNAME hoặc NIFI_PASSWORD chưa được cấu hình")
        
        return dict(username=nifi_username, password=nifi_password)

    @staticmethod
    def get_verify_ssl() -> bool:
        return False
    
    @staticmethod
    def get_request_timeout() -> float:
        nifi_request_timeout = os.getenv("nifi_request_timeout")
        return float(nifi_request_timeout)