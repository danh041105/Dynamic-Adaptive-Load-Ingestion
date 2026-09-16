from dataclasses import dataclass
from typing import Any, Protocol
class _NifiRequester(Protocol):
    def request(self, method: str, path: str, **kwargs: Any) -> Any: ...

@dataclass
class NifiProcessorClient:
    client: _NifiRequester

    def get_processors(self, process_group_id: str) -> Any:
        return self.client.request(
            "GET",
            f"/process-groups/{process_group_id}/processors",
        )

    def get_processor(self, processor_id: str) -> Any:
        return self.client.request(
            "GET",
            f"/processors/{processor_id}",
        )
