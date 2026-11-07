from fastapi import APIRouter

from app.application.container import get_container
from app.application.services.contracts_service import ContractsService

router = APIRouter()


@router.get("/ready")
def readiness() -> dict[str, object]:
    service = ContractsService(container=get_container())
    return service.readiness_snapshot()

