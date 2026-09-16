from dataclasses import dataclass
from typing import Any, Protocol
from backend.config.nifi_config import NifiConfig
import time

class _NifiRequester(Protocol):
    def request(self, method: str, path: str, **kwargs: Any) -> Any: ...

@dataclass
class NifiProcessGroupClient:
    client: _NifiRequester

    def get_root_process_group(self) -> Any:
        return self.client.request(
            "GET", "/flow/process-groups/root")

    def get_process_group(self, process_group_id: str) -> Any:
        return self.client.request("GET", f"/process-groups/{process_group_id}")

    def get_child_process_groups(self, process_group_id: str) -> Any:
        return self.client.request(
            "GET", f"/process-groups/{process_group_id}/process-groups")

    def get_process_group_status(self, process_group_id: str) -> Any:
        return self.client.request("GET", f"/flow/process-groups/{process_group_id}/status")
    
    def set_run_state(self, process_group_id: str, state: str) -> dict | None:
        state = state.upper()
        if state not in {'RUNNING', 'STOPPED'}:
            raise ValueError('state must be RUNNING or STOPPED')
        return self.client.request('PUT', f'/flow/process-groups/{process_group_id}',
                                   json={'id': process_group_id, 'state': state})

    def start_process_group(self, process_group_id: str) -> dict | None:
        return self._ensure_state(process_group_id, 'RUNNING')

    def stop_process_group(self, process_group_id: str) -> dict | None:
        return self._ensure_state(process_group_id, 'STOPPED')

    def wait_for_state(self, process_group_id: str, expected_state: str,
                       timeout_seconds: float, poll_interval_seconds: float) -> dict:
        deadline = time.monotonic() + timeout_seconds
        while True:
            process_group = self.get_process_group(process_group_id)
            if self._is_in_state(process_group, expected_state):
                return process_group
            if time.monotonic() >= deadline:
                raise TimeoutError(f'Process Group {process_group_id} did not reach {expected_state}')
            time.sleep(poll_interval_seconds)

    def _ensure_state(self, process_group_id: str, expected_state: str) -> dict | None:
        process_group = self.get_process_group(process_group_id)
        if self._is_in_state(process_group, expected_state):
            return process_group
        self.set_run_state(process_group_id, expected_state)
        return self.wait_for_state(process_group_id, expected_state, NifiConfig.get_request_timeout(), 1)

    @staticmethod
    def _is_in_state(process_group: dict, expected_state: str) -> bool:
        component = process_group.get('component', {})
        running = component.get('runningCount', 0)
        stopped = component.get('stoppedCount', 0)
        if expected_state == 'RUNNING':
            return running > 0 and stopped == 0
        return running == 0
