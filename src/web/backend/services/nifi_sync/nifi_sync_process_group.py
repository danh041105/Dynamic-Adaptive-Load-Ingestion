import logging
from sqlalchemy.orm import Session
from backend.clients.nifi_client import NifiClient
from backend.models.nifi_process_group import NifiProcessGroup
logger = logging.getLogger(__name__)

class NifiSyncProcessGroup:

    def __init__(self, db: Session, nifi_client: NifiClient) -> None:
        self.db = db
        self.nifi_client = nifi_client

    def sync_process_groups(self) -> dict:
        """
        Đồng bộ toàn bộ Process Group từ NiFi xuống SingleStore.
        """
        try:
            # 1. Đọc root Process Group
            root_response = (self.nifi_client.process_groups.get_root_process_group())
            process_group_flow = root_response.get("processGroupFlow",{})
            root_group_id = process_group_flow.get("id")

            if not root_group_id:
                raise ValueError(
                    "NiFi response không chứa root process group id"
                )

            # 2. Lấy đầy đủ metadata của root
            root_entity = (self.nifi_client.process_groups.get_process_group(root_group_id))

            # 3. Upsert root
            root_db = self._upsert_process_group(entity=root_entity, parent_id=None, level=0)

            # flush để root_db.id có ngay trước khi insert child
            self.db.flush()

            synced_count = 1

            # 4. Đồng bộ đệ quy các child
            synced_count += self._sync_child_process_groups(nifi_parent_id=root_group_id, db_parent_id=root_db.id,level=1)

            # 5. Commit một lần sau khi toàn bộ cây sync thành công
            self.db.commit()

            logger.info(
                "NiFi process group đã đồng bộ: %s groups",
                synced_count,
            )
            return {
                "synced_process_groups": synced_count,
            }

        except Exception:
            self.db.rollback()
            logger.exception(
                "NiFi process group đồng bộ thất bại"
            )
            raise

    def _sync_child_process_groups(self, nifi_parent_id: str, db_parent_id: int, level: int) -> int:
        """
        Đồng bộ các Process Group con trực tiếp của một Process Group
        và tiếp tục đi xuống các cấp thấp hơn.
        """
        response = self.nifi_client.process_groups.get_child_process_groups(nifi_parent_id)

        process_groups = response.get("processGroups", [])

        synced_count = 0

        for entity in process_groups:
            component = entity.get("component") or {}
            child_group_id = (component.get("id") or entity.get("id"))

            if not child_group_id:
                logger.warning(
                    "Skip Process Group vì không có id"
                )
                continue

            # Upsert child
            child_db = self._upsert_process_group(entity=entity, parent_id=db_parent_id, level=level)

            # Cần ID PostgreSQL để child tiếp theo tham chiếu parent
            self.db.flush()

            synced_count += 1

            # Tiếp tục đi xuống cây NiFi
            synced_count += self._sync_child_process_groups(nifi_parent_id=child_group_id, db_parent_id=child_db.id, level=level + 1)

        return synced_count
    
    def _upsert_process_group(self, entity: dict, parent_id: int | None, level: int) -> NifiProcessGroup:

        component = entity.get("component") or {}
        group_id = (component.get("id") or entity.get("id"))
        group_name = component.get("name")
        if not group_id:
            raise ValueError("Process Group entity không chứa id")

        if not group_name:
            raise ValueError(f"Process Group {group_id} không chứa name")

        process_group = self.db.query(NifiProcessGroup).filter(NifiProcessGroup.group_id == group_id).first()

        # Đã tồn tại -> update
        if process_group:
            process_group.group_name = group_name
            process_group.parent_id = parent_id
            process_group.level = level
            return process_group

        # Chưa tồn tại -> insert
        process_group = NifiProcessGroup(group_id=group_id, group_name=group_name, parent_id=parent_id, level=level)
        self.db.add(process_group)

        return process_group