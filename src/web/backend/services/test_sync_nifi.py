from backend.config.database import SessionLocal
from backend.clients.nifi_client import NifiClient
from backend.services.nifi_sync_service import NifiSyncService


db = SessionLocal()

try:
    nifi_client = NifiClient()

    sync_service = NifiSyncService(
        db=db,
        nifi_client=nifi_client,
    )

    result = sync_service.sync_all()

    print("===== SYNC RESULT =====")

    print(
        "Process Groups:",
        result["process_groups"]
    )

    print(
        "Sources:",
        result["sources"]
    )

    print(
        "Components:",
        result["components"]
    )

finally:
    db.close()