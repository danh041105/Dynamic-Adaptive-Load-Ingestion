from datetime import datetime, timezone
from backend.clients.nifi_process_group_client import NifiProcessGroupClient
from typing import Any, Protocol
from dataclasses import dataclass

class _NifiRequester(Protocol):
    def request(self, method: str, path: str, **kwargs: Any) -> Any: ...

@dataclass
class NifiMetricClient:
    client: _NifiRequester

    def get_connection_metric(self, process_group_id: str) -> Any:
        process_group_status = self.client.request(
            "GET",
            f"/flow/process-groups/{process_group_id}/status",
            params={"recursive": "true"}
        )
        # CellTrace 4G HNI/CellTrace ENM hoặc Celltrace Megaplexer
        root = (process_group_status
                        .get("processGroupStatus", {}) # Celltrace 4G HNI"
                        .get("aggregateSnapshot", {}) # CellTrace 4G HNI
                    )

        pair = self._find_fetch_sftp_pair(root)
        if pair is None:
            raise LookupError(
                "Không tìm thấy cặp connection 'unmatched' "
                f"và processor FetchSFTP trong process group {process_group_id}"
            )
        
        unmatched, fetch_sftp = pair

        queued_count = int(unmatched.get("flowFilesQueued") or 0)
        input_files = int(unmatched.get("flowFilesIn") or 0)
        processed_file = int(fetch_sftp.get("flowFilesOut") or 0)
        processed_byte = int(fetch_sftp.get("bytesOut") or 0)

        avg_input_bytes = (
            processed_byte / processed_file
            if processed_file > 0
            else 0.0
        )

        queue_bytes = queued_count * avg_input_bytes
        processor_entity = self.client.request("GET", f"/processors/{fetch_sftp['id']}")

        concurrent_task = int(
            processor_entity
            .get("component", {})
            .get("config", {})
            .get("concurrentlySchedulableTaskCount", 0)
            or 0
        )

        return {
            "queued_count": queued_count,
            "queue_bytes": queue_bytes,
            "input_files": input_files,
            "avg_input_bytes": avg_input_bytes,
            "processed_file": processed_file,
            "processed_byte": processed_byte,
            "concurrent_task": concurrent_task,
        }
    @staticmethod
    def _find_fetch_sftp_pair(group: dict[str, Any])-> tuple[dict[str, Any], dict[str, Any]] | None:
        processors = [
            item.get("processorStatusSnapshot", {})
            for item in group.get("processorStatusSnapshots", [])
        ]
        connections = [
            item.get("connectionStatusSnapshot", {})
            for item in group.get("connectionStatusSnapshots", [])
        ]
        for processor in processors:
            if processor.get("type") != "FetchSFTP":
                continue
            for connection in connections:
                is_unmatched = connection.get("name", "").lower() == "unmatched"
                same_group = connection.get("groupId") == processor.get("groupId")
                feeds_fetch_sftp = connection.get("destinationName") == processor.get("name")
                if is_unmatched and same_group and feeds_fetch_sftp:
                    return connection, processor

        # Tìm tiếp trong các process group con
        for item in group.get("processGroupStatusSnapshots", []):
            child_group = item.get("processGroupStatusSnapshot", {})
            pair = NifiMetricClient._find_fetch_sftp_pair(child_group)

            if pair is not None:
                return pair

        return None