import logging
from sqlalchemy.orm import Session
from backend.clients.nifi_client import NifiClient
from backend.models.nifi_source import NifiSource
from backend.models.nifi_component import NifiComponent

logger = logging.getLogger(__name__)


class NifiSyncComponent:
    def __init__(self, db: Session, nifi_client: NifiClient) -> None:
        self.db = db
        self.nifi_client = nifi_client

    def sync_components(self) -> dict:
        """
        Đồng bộ Processor và Connection của từng source
        xuống bảng nifi_component.
        """
        try:
            sources = self.db.query(NifiSource).all()
            processor_count = 0
            connection_count = 0

            for source in sources:
                # Processors
                processor_response = self.nifi_client.processors.get_processors(source.external_source_id)
                processors = processor_response.get("processors", [])
                for processor in processors:
                    self._upsert_processor(processor=processor, source_id=source.id)
                    processor_count += 1

                # Connections
                connection_response = self.nifi_client.connections.get_connections(source.external_source_id)
                connections = connection_response.get("connections", [])

                for connection in connections:
                    self._upsert_connection(connection=connection, source_id=source.id)
                    connection_count += 1

            self.db.commit()
            synced_count = processor_count + connection_count

            return {
            "synced_components": synced_count,
            "synced_processors": processor_count,
            "synced_connections": connection_count,
            }
        
        except Exception:
            self.db.rollback()
            logger.exception("NiFi component đồng bộ thất bại")
            raise
            
    def _upsert_processor(self, processor: dict, source_id: int) -> NifiComponent:
        # Insert hoặc update một Processor.
        component = processor.get("component") or {}
        component_id = component.get("id") or processor.get("id")
    
        if not component_id:
            raise ValueError("Processor không chứa id")

        component_name = component.get("name")
        processor_type = component.get("type", "")
        processor_type = processor_type.rsplit(".", 1)[-1]
        db_component = self.db.query(NifiComponent).filter(NifiComponent.component_id == component_id).first()

        # UPDATE
        if db_component:
            db_component.source_id = source_id
            db_component.component_name = component_name
            db_component.component_type = "PROCESSOR"
            db_component.destination_component_id = None
            return db_component

        # INSERT
        db_component = NifiComponent(
            source_id=source_id,
            component_id=component_id,
            component_name=component_name,
            component_type="Processor", # FetchSFTP
            source_component_id=None,
            destination_component_id=None,
        )
        self.db.add(db_component)
        return db_component

    def _upsert_connection(self, connection: dict, source_id: int) -> NifiComponent:
        """
        Insert hoặc update một Connection.
        """
        component = connection.get("component") or {}
        component_id = component.get("id") or connection.get("id")

        if not component_id:
            raise ValueError("Connection không chứa id")

        component_name = component.get("name")
        source_component = component.get("source") or {}
        destination_component = component.get("destination") or {}
        source_component_id = source_component.get("id")
        destination_component_id = destination_component.get("id")

        db_component = self.db.query(NifiComponent).filter(NifiComponent.component_id == component_id).first()

        # UPDATE
        if db_component:
            db_component.source_id = source_id
            db_component.component_name = component_name
            db_component.component_type = "Connection" # Unmatched
            db_component.source_component_id = source_component_id
            db_component.destination_component_id = destination_component_id
            return db_component

        # INSERT
        db_component = NifiComponent(
            source_id=source_id,
            component_id=component_id,
            component_name=component_name,
            component_type="CONNECTION",
            source_component_id=source_component_id,
            destination_component_id=destination_component_id
        )
        self.db.add(db_component)

        return db_component