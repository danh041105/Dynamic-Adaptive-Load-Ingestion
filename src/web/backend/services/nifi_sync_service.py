import logging
from sqlalchemy.orm import Session
from dataclasses import dataclass, field
from backend.clients.nifi_client import NifiClient
from backend.services.nifi_sync.nifi_sync_sources import NifiSyncSource
from backend.services.nifi_sync.nifi_sync_process_group import NifiSyncProcessGroup
from backend.services.nifi_sync.nifi_sync_components import NifiSyncComponent

logger = logging.getLogger(__name__)

@dataclass
class NifiSyncService:
    db: Session
    nifi_client: NifiClient
    process_group_sync: NifiSyncProcessGroup = field(init=False)
    source_sync: NifiSyncSource = field(init=False)
    component_sync: NifiSyncComponent = field(init=False)

    def __post_init__(self) -> None:
        self.process_group_sync = NifiSyncProcessGroup(db=self.db, nifi_client=self.nifi_client)
        self.source_sync = NifiSyncSource(db=self.db, nifi_client=self.nifi_client)
        self.component_sync = NifiSyncComponent(db=self.db, nifi_client=self.nifi_client)

    def sync_all(self) -> dict:
        """
        Đồng bộ toàn bộ metadata từ NiFi xuống SingleStore.
        Thứ tự:
        1. Process Group
        2. Source
        3. Component
        """
        try:
            logger.info("Bắt đầu đồng bộ metadata NiFi")
            process_group_result = self.process_group_sync.sync_process_groups()
            source_result = self.source_sync.sync_sources()
            component_result = self.component_sync.sync_components()
            result = {
            "process_groups": process_group_result,
            "sources": source_result,
            "components": component_result,
            }
            logger.info("Đồng bộ toàn bộ metadata NiFi thành công")
            return result
        
        except Exception:
            logger.exception("Đồng bộ metadata NiFi thất bại")
            raise