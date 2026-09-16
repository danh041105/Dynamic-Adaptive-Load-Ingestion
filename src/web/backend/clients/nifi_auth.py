from dataclasses import dataclass, field
import requests
from backend.clients.exceptions import (
    NifiAuthenticationError,
    NifiConnectionError,
    NifiResponseError,
    NifiTimeoutError,
)

@dataclass
class NifiAuth:
    base_url: str
    login_payload: dict[str, str] = field(repr=False)
    session: requests.Session = field(repr=False)
    verify: bool | str = True
    timeout: float = 10.0

    # Token chỉ tồn tại trong RAM và không xuất hiện trong repr/log.
    _access_token: str | None = field(init=False, default=None, repr=False)

    def authenticate(self) -> str:
        path = "/access/token"
        url = f"{self.base_url.rstrip('/')}{path}"

        try:
            response = self.session.post(
                url=url,
                data=self.login_payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/plain",
                },
                timeout=self.timeout,
                verify=self.verify,
            )
        except requests.Timeout as exc:
            raise NifiTimeoutError("NiFi authentication timeout") from exc
        except requests.RequestException as exc:
            # Bao gồm connection, DNS và TLS/SSL errors.
            raise NifiConnectionError(
                "Không thể kết nối tới NiFi khi authenticate"
            ) from exc

        if response.status_code in {400, 401, 403}:
            raise NifiAuthenticationError(
                "NiFi authentication thất bại"
            )

        if not response.ok:
            raise NifiResponseError.from_response(
                method="POST",
                path=path,
                response=response,
            )

        token = response.text.strip()
        if not token:
            raise NifiResponseError(
                status_code=response.status_code,
                method="POST",
                path=path,
                response_detail="NiFi trả access token rỗng",
            )

        self._access_token = token
        return token

    def get_access_token(self) -> str:
        if self._access_token is None:
            return self.authenticate()
        return self._access_token

    def invalidate_token(self) -> None:
        self._access_token = None

    def authorization_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Accept": "application/json",
        }
