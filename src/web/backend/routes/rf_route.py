from fastapi import APIRouter, Depends
from backend.dependencies.auth_dependencies import require_roles
from backend.constants.enums import UserRole

router = APIRouter(
    prefix="/radio-frequency-engineer",
    tags=["Radio Frequency Engineer"],
    dependencies=[Depends(require_roles(UserRole.RADIO_FREQUENCY_ENGINEER))]
)