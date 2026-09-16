# Task: Xử lý download request và bật/tắt ENM trên NiFi

## 1. Mục tiêu

Hoàn thiện luồng xử lý download request từ lúc RF Engineer gửi yêu cầu đến khi backend điều khiển ENM tương ứng trên NiFi và cập nhật kết quả cuối cùng.

Trong phạm vi task này:

- Một ENM được biểu diễn bởi một bản ghi `nifi_source`.
- `nifi_source.external_source_id` là ID process group tương ứng trên NiFi.
- Khi đến `start_time`, hệ thống chuyển process group của ENM sang `RUNNING`.
- Khi đến `end_time`, hệ thống chuyển process group sang `STOPPED` và hoàn thành request.
- 

## 2. Luồng nghiệp vụ

1. RF Engineer gửi `POST /radio-frequency-engineer/requests` với `source_id`, `start_time` và `end_time`.
2. Backend xác thực người dùng và kiểm tra role `Radio Frequency Engineer`.
3. Backend kiểm tra:
   - `start_time < end_time`;
   - source tồn tại;
   - source có `external_source_id`;
   - source có thể nhận yêu cầu;
   - không có request khác của cùng source bị trùng thời gian và đang hoạt động.

4. Backend lưu request với trạng thái `PENDING`.
5. Worker định kỳ lấy các request đến thời điểm chạy.
6. Worker khóa/claim request, chuyển trạng thái sang `RECEIVED`, sau đó gọi NiFi để bật process group ENM.
7. Khi NiFi xác nhận process group đã chạy, worker cập nhật:
   - `status = PROCESSING`;
   - `started_at = thời điểm thực tế bắt đầu`.
8. Khi đến `end_time`, worker gọi NiFi để dừng process group.
9. Khi NiFi xác nhận process group đã dừng, worker cập nhật:
   - `status = COMPLETED`;
   - `completed_at = thời điểm thực tế hoàn thành`.
10. Nếu thao tác NiFi thất bại sau số lần retry cho phép, worker cập nhật `FAILED` và ghi nguyên nhân vào `failure_reason`.

## 3. Yêu cầu triển khai

### 3.1 Sửa kiểm tra source nhận request

- Không truy cập thuộc tính chưa tồn tại như luồng hiện tại trong `DownloadRequestService._validate_source_accepting_requests()`.
- Trả `409 Conflict` khi source không thể nhận request.
- Trả `404 Not Found` khi source không tồn tại.
- Trả lỗi nghiệp vụ rõ ràng nếu source chưa được ánh xạ với process group NiFi.

### 3.2 Kiểm tra thời gian và xung đột request

- Từ chối request nếu `start_time >= end_time`.
- Chuẩn hóa và lưu datetime có timezone; không trộn datetime naive và timezone-aware.
- Từ chối khoảng thời gian đã kết thúc tại thời điểm tạo request.
- Nhiều request của cùng source được phép có khoảng thời gian giao nhau 
- Process group là tài nguyên dùng chung theo source: request đầu tiên cần source thì đảm bảo process group RUNNING;
khi một request kết thúc, chỉ STOP process group nếu không còn request PROCESSING hợp lệ nào khác của source đó.
- Các trạng thái được xem là đang hoạt động: `PENDING`, `RECEIVED`, `PROCESSING`.

Hai khoảng thời gian xung đột khi:

```text
new_start < existing_end AND new_end > existing_start
```

### 3.3 Mở rộng NiFi client

Thêm các hàm vào `NifiProcessGroupClient`:

```python
def set_run_state(process_group_id: str, state: str) -> dict | None: ...
def start_process_group(process_group_id: str) -> dict | None: ...
def stop_process_group(process_group_id: str) -> dict | None: ...
def wait_for_state(
    process_group_id: str,
    expected_state: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict: ...
```

Yêu cầu:

- Sử dụng NiFi REST API để điều khiển toàn bộ processor trong process group.
- Payload phải dùng đúng ID process group và trạng thái `RUNNING` hoặc `STOPPED`.
- Sau lệnh start/stop, đọc lại trạng thái đến khi đạt trạng thái mong muốn hoặc timeout.
- Tái sử dụng `NifiClient.request()` để giữ chung authentication, timeout và xử lý lỗi.
- Không ghi token hoặc mật khẩu NiFi vào log.
- Phân biệt lỗi kết nối, timeout, xác thực và lỗi phản hồi NiFi.

### 3.4 Worker xử lý vòng đời request

Tạo service xử lý nghiệp vụ độc lập với FastAPI route, ví dụ:

```text
backend/services/download_request_processor.py
```

Service cần cung cấp tối thiểu:

```python
process_due_requests()
start_request(request_id: int)
complete_due_requests()
fail_request(request_id: int, reason: str)
```

Yêu cầu worker:

- Chạy ngoài request HTTP; API tạo request không chờ ENM chạy xong.
- Poll database theo chu kỳ cấu hình được.
- Claim request theo cách an toàn để nhiều worker không xử lý cùng một request.
- Commit trạng thái trước/sau các thao tác bên ngoài một cách rõ ràng.
- Có retry với backoff cho lỗi NiFi tạm thời.
- Các thao tác start/stop phải idempotent: ENM đã `RUNNING` thì start được xem là thành công; đã `STOPPED` thì stop được xem là thành công.
- Khi tiến trình khởi động lại, các request `RECEIVED` hoặc `PROCESSING` phải có thể tiếp tục/reconcile, không bị treo vĩnh viễn.
- Không giữ database transaction mở trong suốt thời gian chờ NiFi.

Cơ chế chạy worker có thể dùng scheduler/worker framework hiện có. Nếu codebase chưa có framework, tạo command/process riêng có vòng poll cấu hình được; không chạy vòng lặp vô hạn trực tiếp trong FastAPI request handler.

### 3.5 Trạng thái request

Chỉ sử dụng các trạng thái trong `DownloadRequestStatus`:

```text
PENDING -> RECEIVED -> PROCESSING -> COMPLETED
                                  -> FAILED
                    -> FAILED
```

- Không ghi các giá trị ngoài enum như `SCHEDULED`, `RUNNING` hoặc `DOWNLOADING` vào `download_request.status`.
- Mọi lỗi cuối cùng phải có `failure_reason`.
- `started_at` chỉ được đặt khi ENM thực sự bắt đầu chạy.
- `completed_at` được đặt khi request kết thúc ở `COMPLETED` hoặc `FAILED`.

### 3.6 API và endpoint demo

- Giữ endpoint chính:
  - `POST /radio-frequency-engineer/requests`;
  - `GET /radio-frequency-engineer/requests`;
  - `GET /radio-frequency-engineer/requests/{request_id}`.
- API tạo request trả `201 Created` sau khi lưu thành công, không khẳng định ENM đã bật.
- Response phải phản ánh trạng thái thật trong database.
- Loại bỏ hoặc chuyển các endpoint demo trong `src/web/run_server.py` sang sử dụng cùng controller/service chính.
- Không bypass authentication, validation hoặc gán user mặc định.
- Không đăng ký `download_request_router` hai lần.

## 4. Xử lý đồng thời và an toàn

- Một source chỉ được một request điều khiển tại cùng thời điểm.
- Việc kiểm tra xung đột và tạo request phải chống race condition ở mức database/transaction.
- Worker chỉ xử lý request mà nó claim thành công.
- Không tự động dừng ENM nếu process group đang được một request hợp lệ khác sở hữu.
- Giới hạn độ dài `failure_reason` trước khi lưu database.
- Log phải chứa `request_id`, `source_id`, `external_source_id`, hành động và kết quả; không chứa credential. Trong đó, `external_source_id` chính là ID process group trên NiFi 

## 5. Cấu hình

Bổ sung cấu hình qua environment variable với giá trị mặc định hợp lý:

```text
DOWNLOAD_REQUEST_POLL_INTERVAL_SECONDS
DOWNLOAD_REQUEST_MAX_RETRIES
DOWNLOAD_REQUEST_RETRY_BACKOFF_SECONDS
NIFI_STATE_CHANGE_TIMEOUT_SECONDS
NIFI_STATE_POLL_INTERVAL_SECONDS
```

Validate cấu hình ngay khi khởi tạo và báo lỗi rõ ràng nếu giá trị không hợp lệ.

## 6. Kiểm thử bắt buộc

### Unit test

- Tạo request hợp lệ trả trạng thái `PENDING`.
- Source không tồn tại trả `404`.
- Source không nhận request trả `409`.
- `start_time >= end_time` trả `422`.
- Khoảng thời gian đã kết thúc bị từ chối.
- Hai request cùng source trùng thời gian bị từ chối.
- Request của hai source khác nhau có thể chạy đồng thời.
- NiFi client gửi đúng method, path và payload khi start/stop.
- Start/stop idempotent khi process group đã ở trạng thái mong muốn.
- Timeout hoặc lỗi NiFi làm request chuyển `FAILED` sau retry.
- Worker không xử lý một request hai lần khi có nhiều worker.

### Integration test

- Luồng thành công:
  `POST request -> PENDING -> RECEIVED -> PROCESSING -> COMPLETED`.
- Kiểm tra `started_at` và `completed_at` được ghi đúng thời điểm chuyển trạng thái.
- Kiểm tra phục hồi request đang dở sau khi worker restart.
- Mock NiFi trong automated test; smoke test với NiFi thật phải được tách riêng và chỉ chạy khi có cấu hình rõ ràng.

## 7. Tiêu chí nghiệm thu

- RF Engineer tạo được request hợp lệ qua API chính.
- Request được lưu `PENDING` và có thể xem bằng API list/detail.
- Đến `start_time`, đúng process group tương ứng với ENM được chuyển sang `RUNNING`.
- Đến `end_time`, process group được chuyển sang `STOPPED` và request thành `COMPLETED`.
- Khi NiFi không khả dụng, request được retry và cuối cùng chuyển `FAILED` với nguyên nhân đọc được.
- Không có request bị thực thi hai lần khi chạy nhiều worker.
- Không tồn tại trạng thái request ngoài enum quy định.
- Endpoint demo không còn bypass luồng nghiệp vụ chính.
- Toàn bộ unit test và integration test liên quan đều pass.
- Tài liệu hướng dẫn chạy API, worker và các environment variable được cập nhật.


## 28. Tiêu chí nghiệm thu
- Endpoint `/radio-frequency-engineer/...` được giữ nguyên.
- RF Engineer tạo request thành công.
- Request lưu PostgreSQL với `PENDING`.
- Request được xử lý đúng `start_time`.
- Lifecycle đúng enum.
- Nhiều request cùng source overlap đúng.
- Không start NiFi thừa.
- Không stop source khi request khác còn cần.
- Request cuối cùng mới stop source.
- Nhiều worker không duplicate request.
- Cùng source không bị điều khiển đồng thời.
- PostgreSQL vẫn là source of truth.
- Cache không ảnh hưởng correctness.
- Không log credential.
- Không bypass auth.
- Không sửa backend ngoài phạm vi cần thiết.
- Không refactor code đang hoạt động nếu không cần.
- Unit test và integration test pass.
