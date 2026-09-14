from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.config.nifi_config import get_secret_key, get_algorithm, get_access_token_expire_minutes
from backend.models.user import User
from backend.schemas.auth_schemas import UserRole, TokenResponse

pwd_context= CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    # Tạo tài khoản
    @staticmethod
    def register_user(db: Session, username: str, password: str, role: UserRole) -> object:
        existing_user = db.query(User).filter(User.username==username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username đã tồn tại"
            )
        
        hashed_password = AuthService.hash_password(password)
        new_user = User(username=username, hashed_password=hashed_password, role=role.value)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    # mã hóa mật khẩu người dùng
    @staticmethod
    def hash_password(password: str)-> str: # mã hóa mật khẩu người dùng
        return pwd_context.hash(password)

    # kiểm tra mật khẩu người dùng
    @staticmethod
    def verify_password(plain_password:str, hashed_pasword: str) -> bool: 
        return pwd_context.verify(plain_password, hashed_pasword)

    # lưu token của user sau khi đăng nhập thành công
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = (datetime.now(timezone.utc) + timedelta(minutes=get_access_token_expire_minutes()))
        
        to_encode.update({"exp":expire})
        encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=get_algorithm())

        return encoded_jwt

    # giải mã token của user
    @staticmethod
    def decode_access_token(token: str) -> dict | None: 
        try:
            payload = jwt.decode(token, get_secret_key(), algorithms=[get_algorithm()])
            return payload
        except JWTError:
            return None

    # Kiểm tra đăng nhập của user
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        # Tìm user trong db
        user = db.query(User).filter(User.username == username).first()

        # Kiểm tra đồng thời user và mật khẩu
        if user is None or not AuthService.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mật khẩu đã nhập không chính xác"
            )

        # Tạo access token
        access_token = AuthService.create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        }
    )
        return TokenResponse(access_token=access_token)

