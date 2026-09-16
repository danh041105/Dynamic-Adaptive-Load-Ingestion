from dataclasses import dataclass
from typing import Any, Protocol
from dataclasses import dataclass

class _NifiRequester(Protocol):
    def request(self, method: str, path: str, **kwargs: Any) -> Any: ...


@dataclass
class NifiConnectionClient:

    client: _NifiRequester
    def get_connections(self, process_group_id: str) -> Any:
        return self.client.request(
            "GET",
            f"/process-groups/{process_group_id}/connections",
        )

    def get_flow_connections(self, connection_id: str) -> Any:
        return self.client.request(
            "GET",
            f"flow/connections/{connection_id}/status"
        )