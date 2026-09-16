from fastapi import APIRouter, Depends

from backend.dependencies.auth_dependencies import require_roles
from backend.constants.enums import UserRole

router = APIRouter(
    prefix="/data-engineer",
    tags=["Data Engineer"],
    dependencies=[Depends(require_roles(UserRole.DATA_ENGINEER))]
)