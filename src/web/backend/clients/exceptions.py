from dataclasses import dataclass
class NifiClientError(Exception):
    """Base exception cho tất cả lỗi NiFi client."""


class NifiAuthenticationError(NifiClientError):
    """Sai credentials hoặc authentication thất bại."""


class NifiConnectionError(NifiClientError):
    """Không thể kết nối tới NiFi."""


class NifiTimeoutError(NifiClientError):
    """Request tới NiFi bị timeout."""


@dataclass
class NifiResponseError(NifiClientError):
    status_code: int
    method: str
    path: str
    response_detail: str | None = None

    def __post_init__(self):
        # Tự động gọi Exception.__init__ sau khi dataclass khởi tạo xong thuộc tính
        super().__init__(
            f"NiFi API lỗi {self.status_code} {self.method} {self.path}: {self.response_detail}"
        )

    @classmethod
    def from_response(cls, method: str, path: str, response):
        """Khởi tạo lỗi trực tiếp từ đối tượng response của thư viện HTTP."""
        return cls(
            status_code=response.status_code,
            method=method,
            path=path,
            response_detail=response.text,
        )