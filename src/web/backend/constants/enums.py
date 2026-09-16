from enum import Enum

class UserRole(str, Enum):
    DATA_ENGINEER = "Data Engineer"
    RADIO_FREQUENCY_ENGINEER = "Radio Frequency Engineer"


class DownloadRequestStatus(str, Enum):
    PENDING = "PENDING" # Yêu cầu đang trong hàng chờ
    RECEIVED = "RECEIVED" # Yêu cầu đã được tiếp nhận
    PROCESSING = "PROCESSING" # Yêu cầu đang được xử lý
    COMPLETED = "COMPLETED" # Yêu cầu đã dược hoàn thiện
    FAILED = "FAILED"

class SourceAvailability(str, Enum):
    AVAILABLE = "AVAILABLE" # có thể download file được không ?
    # BUSY = "BUSY"
    # HIGH_LOAD = "HIGH_LOAD"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"

class SourceLoadLevel(str, Enum):
    # NORMAL = "NORMAL"
    # MEDIUM = "MEDIUM"
    # HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"