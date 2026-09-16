import logging
import re
from sqlalchemy.orm import Session
from backend.clients.nifi_client import NifiClient
from backend.models.nifi_process_group import NifiProcessGroup
from backend.models.nifi_source import NifiSource

logger = logging.getLogger(__name__)

class NifiSyncSource:
    def __init__(self, db: Session, nifi_client: NifiClient) -> None:
        self.db = db
        self.nifi_client = nifi_client

    def sync_sources(self) -> dict:
        """
        Đồng bộ các source từ NiFi xuống bảng nifi_source.
        Ví dụ source có source_name là ENM01 --> Nhánh process_group cuối cùng của Download
        """
        try:
            process_groups = self.db.query(NifiProcessGroup).all()

            # Một group là leaf khi id của nó không xuất hiện ở parent_id của group khác.
            parent_ids = {
                process_group.parent_id
                for process_group in process_groups
                if process_group.parent_id is not None
            }
            leaf_groups = {
                process_group 
                for process_group in process_groups
                if process_group.id not in parent_ids
            }

            synced_count = 0
            for process_group in leaf_groups:
                # Lấy ra các Processor trong Process Groups
                response = self.nifi_client.processors.get_processors(process_group.group_id)
                processors = response.get("processors", [])

                # Tạo list kiểm tra xem có processor nào là ListSFTP không 
                
                sftp_processor = None
                for processor in processors:
                    if self._processor_class(processor) == "ListSFTP":
                        sftp_processor = processor
                        break

                if sftp_processor is None: continue
                component = sftp_processor.get("component") or {}
                config = component.get("config") or {}
                properties = config.get("properties") or {}
                remote_path = properties.get("Remote Path")
                source_name = self._extract_source_name(remote_path)

                if not source_name:
                    logger.warning(
                        "Không xác định được source_name của Process Group %s "
                        "từ remote_path=%s",
                        process_group.group_name,
                        remote_path,
                    )
                    continue

                status = component.get("state")
                
                self._upsert_source(process_group=process_group, source_name=source_name, remote_path=remote_path, status=status)
                synced_count += 1

            self.db.commit()
            logger.info("NiFi source đã đồng bộ: %s sources", synced_count)

            return {
                "synced_sources": synced_count,
            }
        
        except Exception:
            self.db.rollback()
            logger.exception("NiFi source đồng bộ thất bại")
            raise

    def _processor_class(self, processor: dict) -> str:
        component = processor.get("component") or {}
        processor_type = component.get("type", "")

        # Nếu processor có dạng là: "org.apache.nifi.processors.standard.ListSFTP" thì nó sẽ trả về ListSFTP
        return processor_type.rsplit(".", 1)[-1]

    def _extract_source_name(self, remote_path: str | None) -> str | None:
        # Ví dụ: /cell_trace_server/ericsson/enm01/CELLTRACE -> ENM01
        if not remote_path: return None
        
        match = re.search(r"/(ENM\d+|MGPL\d+|)(?:/|$)", remote_path, re.IGNORECASE)
        if not match: 
            return None
        
        return match.group(1).upper()

    def _extract_vendor(self, remote_path: str | None) -> str | None: 
        # Ví dụ: /cell_trace_server/ericsson/enm01/CELLTRACE -> ericsson
        if not remote_path: return None

        match = re.search(r"/(ericsson|nokia)(?:/|$)", remote_path, re.IGNORECASE)

        if not match: 
            return None
        return match.group(1).lower()

    def _upsert_source(self, process_group: NifiProcessGroup, source_name: str, 
                    remote_path: str | None, status: str | None) -> NifiSource:
        
        vendor = self._extract_vendor(remote_path)
        # Một Process Group tương ứng với một source
        source = self.db.query(NifiSource).filter(NifiSource.process_group_id == process_group.id).first()
        
        # update
        if source:
            source.external_source_id = process_group.group_id
            source.name = source_name
            source.remote_path = remote_path
            source.vendor = vendor
            source.status = status

            return source

        # insert
        source = NifiSource(
            external_source_id=process_group.group_id,
            name=source_name,
            process_group_id=process_group.id,
            vendor=vendor,
            remote_path=remote_path,
            status=status
        )
        self.db.add(source)

        return source