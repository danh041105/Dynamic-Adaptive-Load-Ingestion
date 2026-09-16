from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.user import User
from backend.services.auth_service import AuthService
from collections.abc import Callable
from backend.constants.enums import UserRole


bearer_scheme = HTTPBearer(auto_error=False)

def unauthorized_exception(detail: str = "Token không hợp lệ hoặc đã hết hạn") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:

    # Không có Authorization header
    # hoặc Authorization không phải Bearer
    if credentials is None:
        raise unauthorized_exception("Chưa đăng nhập")

    # Kiểm tra scheme
    if credentials.scheme.lower() != "bearer":
        raise unauthorized_exception("Authorization phải sử dụng Bearer token")

    # Decode và verify JWT
    payload = AuthService.decode_access_token(credentials.credentials)

    # Token sai, hết hạn hoặc thiếu sub
    if payload is None:
        raise unauthorized_exception()    
      
    sub = payload.get("sub")
    if sub is None:
        raise unauthorized_exception("Token thiếu thông tin người dùng")

     # sub bắt buộc phải chuyển được thành user_id
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise unauthorized_exception("Token không hợp lệ")

    # Query vào db để xác định user
    user = db.query(User).filter(User.id == user_id).first()

    # Token có thể còn sống nhưng user đã bị xóa
    if user is None:
        raise unauthorized_exception("Người dùng không tồn tại")
    return user


def require_roles(*allowed_roles: UserRole) -> Callable:

    allowed_values = {
        role.value for role in allowed_roles
    }
    def check_role(current_user: User = Depends(get_current_user)) -> User:

        # Role trong database không thuộc UserRole hợp lệ
        try:
            current_role = UserRole(current_user.role)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role của người dùng không hợp lệ",
            )

        if current_role.value not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này",
            )
        return current_user
    return check_role