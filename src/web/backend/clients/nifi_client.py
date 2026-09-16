from dataclasses import dataclass, field
from typing import Any
import requests
from backend.clients.exceptions import (
    NifiAuthenticationError,
    NifiConnectionError,
    NifiResponseError,
    NifiTimeoutError,
)
from backend.clients.nifi_auth import NifiAuth
from backend.clients.nifi_connection_client import NifiConnectionClient
from backend.clients.nifi_process_group_client import NifiProcessGroupClient
from backend.clients.nifi_processor_client import NifiProcessorClient
from backend.config.nifi_config import NifiConfig


@dataclass
class NifiClient:
    # Dependency có thể inject khi unit test.
    config: type[NifiConfig] = NifiConfig
    session: requests.Session = field(
        default_factory=requests.Session,
        repr=False,
    )

    base_url: str = field(init=False)
    login_payload: dict[str, str] = field(init=False, repr=False)
    verify: bool | str = field(init=False)
    timeout: float = field(init=False)

    auth: NifiAuth = field(init=False, repr=False)
    process_groups: NifiProcessGroupClient = field(init=False)
    processors: NifiProcessorClient = field(init=False)
    connections: NifiConnectionClient = field(init=False)

    def __post_init__(self) -> None:
        self.base_url = self.config.get_nifi_url().rstrip("/")
        self.login_payload = self.config.get_nifi_login_payload()
        self.verify = self.config.get_verify_ssl()
        self.timeout = self.config.get_request_timeout()

        # Tất cả sub-client dùng chung một HTTP session.
        self.auth = NifiAuth(
            base_url=self.base_url,
            login_payload=self.login_payload,
            session=self.session,
            verify=self.verify,
            timeout=self.timeout,
        )

        self.process_groups = NifiProcessGroupClient(self)
        self.processors = NifiProcessorClient(self)
        self.connections = NifiConnectionClient(self)

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        _authentication_retry: bool = True,
    ) -> Any:
        method = method.upper()
        normalized_path = "/" + path.lstrip("/")
        url = f"{self.base_url}{normalized_path}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                headers=self.auth.authorization_headers(),
                timeout=self.timeout,
                verify=self.verify,
            )
        except requests.Timeout as exc:
            raise NifiTimeoutError(
                f"NiFi timeout: {method} {normalized_path}"
            ) from exc
        except requests.RequestException as exc:
            raise NifiConnectionError(
                f"Không thể kết nối NiFi: {method} {normalized_path}"
            ) from exc

        # 401: token có thể hết hạn -> authenticate lại đúng một lần.
        if response.status_code == 401:
            if not _authentication_retry:
                raise NifiAuthenticationError(
                    "Authentication thất bại sau khi retry"
                )

            self.auth.invalidate_token()
            self.auth.authenticate()

            return self.request(
                method=method,
                path=normalized_path,
                params=params,
                json=json,
                data=data,
                _authentication_retry=False,
            )

        # 403/404/409/... không authenticate lại.
        if not response.ok:
            raise NifiResponseError.from_response(
                method=method,
                path=normalized_path,
                response=response,
            )

        if not response.content:
            return None

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type or "+json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise NifiResponseError(
                    status_code=response.status_code,
                    method=method,
                    path=normalized_path,
                    response_detail=(
                        "Response khai báo JSON nhưng parse thất bại"
                    ),
                ) from exc

        return response.text
