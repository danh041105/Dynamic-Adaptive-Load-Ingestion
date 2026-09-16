> Để có thể thực hiện .codex\skills\dashboard\rf\_engineer\_ui\_requirements.md. Phần backend tôi cần phải code những gì

<details><summary>2 previous messages</summary>

> Mình sẽ đối chiếu tài liệu UI RF Engineer với backend hiện có, rồi lập danh sách cụ thể theo endpoint, schema, model và migration cần làm. Mình chỉ phân tích và hướng dẫn, không chỉnh code.
>
> Tài liệu yêu cầu bốn nhóm dữ liệu chính: tổng quan dashboard, danh mục/trạng thái source, vòng đời download request và recommendation. Backend hiện mới có authentication; các bảng SQL đã có khung `nifi_source`, `download_request`, `metric_history`, nhưng chưa có ORM/service/API tương ứng. Mình kiểm tra tiếp pipeline đang ghi các bảng này thế nào để tránh đề xuất endpoint không khớp dữ liệu thực tế.
</details>

Để triển khai giao diện trong [rf_engineer_ui_requirements.md](<./.codex/skills/dashboard/rf_engineer_ui_requirements.md>), backend hiện tại còn thiếu gần như toàn bộ API nghiệp vụ. Hiện mới có authentication và kiểm tra role cơ bản.

## 1. Chuẩn hóa authentication và phân quyền trước

Phần bạn đã làm gồm:

- `UserRole`
- Role trong signup
- `get_current_user()`
- `require_roles()`

Nên bổ sung:

```http
GET /auth/me
Authorization: Bearer <token>
```

Response:

```json
{
  "user_id": 12,
  "username": "rf_engineer01",
  "role": "Radio Frequency Engineer"
}
```

Frontend dùng endpoint này để xác định giao diện sau khi tải lại trang.

Mọi endpoint `/radio/*` đều cần:

```python
Depends(
    require_roles(UserRole.RADIO_FREQUENCY_ENGINEER)
)
```

Lưu ý tên role trong tài liệu có lúc là `Radio Engineer`, còn code là `Radio Frequency Engineer`. Nên thống nhất một giá trị duy nhất.

## 2. Tạo SQLAlchemy model nghiệp vụ

Database đã có bảng nhưng backend chưa có ORM model. Cần tạo:

```text
models/
├── nifi_source.py
├── download_request.py
└── metric_history.py
```

### `NifiSource`

Ánh xạ bảng `nifi_source`:

```text
id
source_id
source_name
process_group_id
vendor
remote_path
schedule_start
schedule_end
status
```

### `DownloadRequest`

Ánh xạ bảng `download_request`:

```text
id
user_id
source_id
start_time
end_time
status
created_at
started_at
completed_at
failure_reason
```

Thiết lập relationship:

```text
User 1 ─── N DownloadRequest N ─── 1 NifiSource
```

### `MetricHistory`

Dùng để lấy metric gần nhất của source:

```text
source_id
recorded_at
queued_count
queue_bytes
input_file_rate
processed_file_rate
concurrent_tasks
```

## 3. Bổ sung trường recommendation

Bảng `download_request` hiện chưa lưu được recommendation trong yêu cầu UI. Nên bổ sung:

```sql
ALTER TABLE download_request
ADD COLUMN recommended_start_time TIMESTAMP,
ADD COLUMN recommended_end_time TIMESTAMP,
ADD COLUMN recommendation_reason TEXT,
ADD COLUMN recommendation_accepted BOOLEAN;
```

Tuy nhiên cần làm rõ một điểm nghiệp vụ quan trọng:

- `start_time/end_time` là khoảng dữ liệu Cell Trace cần lấy.
- Thời điểm hệ thống thực sự chạy download là một khái niệm khác.

Nếu người dùng muốn dữ liệu từ `10:00–12:00`, không nên tự đổi thành dữ liệu `10:30–12:30` chỉ vì hệ thống quá tải. Tốt hơn nên thêm:

```sql
scheduled_at TIMESTAMP;
recommended_scheduled_at TIMESTAMP;
```

Như vậy backend giữ nguyên khoảng dữ liệu nhưng đề xuất thời điểm xử lý khác.

## 4. Định nghĩa trạng thái bằng enum

Không nên dùng chuỗi tự do. Tạo enum:

```python
class DownloadRequestStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
```

Thêm `CHECK CONSTRAINT` tương ứng trong PostgreSQL.

Chỉ backend/worker được thay đổi status; frontend không được gửi status khi tạo request.

Luồng hợp lệ:

```text
PENDING → SCHEDULED → RUNNING → COMPLETED
                         └────→ FAILED

PENDING → REJECTED
```

## 5. API danh sách source và availability

### Danh sách source

```http
GET /radio/sources
```

Response:

```json
[
  {
    "id": 6,
    "source_code": "ENM06",
    "source_name": "ENM06",
    "vendor": "Ericsson",
    "availability": "BUSY",
    "load_level": "HIGH",
    "accepting_requests": true
  }
]
```

Không nên trả trực tiếp toàn bộ metric kỹ thuật cho RF Engineer.

### Chi tiết source

```http
GET /radio/sources/{source_id}
```

### Kiểm tra trước khi tạo request

```http
POST /radio/download-requests/assess
```

Request:

```json
{
  "source_id": 6,
  "start_time": "2026-09-14T10:00:00+07:00",
  "end_time": "2026-09-14T12:00:00+07:00"
}
```

Response:

```json
{
  "available": true,
  "source_status": "BUSY",
  "load_level": "HIGH",
  "can_submit_original": true,
  "recommendation": {
    "scheduled_at": "2026-09-14T12:30:00+07:00",
    "reason": "Source đang có tải cao"
  }
}
```

## 6. Logic tính trạng thái source

Tạo một service riêng:

```text
services/source_availability_service.py
```

Service đọc:

- `nifi_source.status`
- Bản ghi `metric_history` mới nhất
- `queued_count`
- `queue_bytes`
- Tỷ lệ input/processed
- Thời gian metric cuối cùng được cập nhật

Sau đó tổng hợp thành:

```text
AVAILABLE
BUSY
HIGH_LOAD
UNAVAILABLE
```

Các ngưỡng nên để trong config, ví dụ:

```python
HIGH_QUEUE_COUNT = 50_000
BUSY_QUEUE_COUNT = 10_000
METRIC_STALE_MINUTES = 5
```

Nếu metric quá cũ, nên trả `UNAVAILABLE` hoặc `UNKNOWN`, không nên coi là `AVAILABLE`.

## 7. API tạo download request

```http
POST /radio/download-requests
```

Request:

```json
{
  "source_id": 6,
  "start_time": "2026-09-14T10:00:00+07:00",
  "end_time": "2026-09-14T12:00:00+07:00",
  "accept_recommendation": false
}
```

Backend cần kiểm tra:

- User đúng role.
- Source tồn tại.
- `start_time < end_time`.
- Khoảng thời gian không vượt giới hạn cho phép.
- Source có nhận request hay không.
- Không tạo request trùng lặp.
- Chạy lại availability check — không được chỉ tin kết quả frontend kiểm tra trước đó.

Khi tạo:

```text
user_id = current_user.id
status = PENDING
```

Frontend tuyệt đối không được tự truyền `user_id`.

## 8. API My Requests

```http
GET /radio/download-requests
```

Query parameters đề xuất:

```text
status
source_id
page
page_size
sort
```

Mọi câu query phải có:

```python
DownloadRequest.user_id == current_user.id
```

Response nên có pagination:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

Không trả request của user khác, kể cả user đoán được ID.

## 9. API chi tiết request

```http
GET /radio/download-requests/{request_id}
```

Câu query cần đồng thời kiểm tra:

```python
DownloadRequest.id == request_id
DownloadRequest.user_id == current_user.id
```

Nếu request thuộc người khác, nên trả `404` thay vì `403` để tránh tiết lộ request đó tồn tại.

Response:

```json
{
  "id": 105,
  "source": {
    "id": 6,
    "name": "ENM06",
    "vendor": "Ericsson"
  },
  "start_time": "...",
  "end_time": "...",
  "status": "FAILED",
  "created_at": "...",
  "started_at": "...",
  "completed_at": "...",
  "failure_reason": "Source không phản hồi",
  "recommendation": null
}
```

Không trả `concurrent_tasks` hoặc allocation nội bộ.

## 10. API Download History

```http
GET /radio/download-requests/history
```

Bộ lọc:

```text
source_id
from_date
to_date
status
page
page_size
```

Backend tự giới hạn status lịch sử:

```text
COMPLETED
FAILED
REJECTED
```

Và vẫn chỉ lấy request của `current_user`.

## 11. API dashboard

```http
GET /radio/dashboard
```

Nên gom toàn bộ dữ liệu cần cho dashboard trong một request:

```json
{
  "summary": {
    "active_requests": 2,
    "recent_completed_requests": 5
  },
  "system_status": {
    "active_sources": 6,
    "total_sources": 10,
    "load_level": "MODERATE"
  },
  "active_requests": [],
  "frequent_sources": [],
  "recent_history": [],
  "recommendations": []
}
```

“Source thường xuyên sử dụng” có thể tính bằng:

```sql
COUNT(download_request.id)
GROUP BY source_id
WHERE user_id = current_user.id
ORDER BY COUNT(*) DESC
LIMIT 3;
```

## 12. Worker xử lý request

API chỉ tạo bản ghi `PENDING`; cần một worker hoặc Airflow DAG để thực sự xử lý:

1. Đọc request `PENDING`.
2. Đánh giá tài nguyên.
3. Chuyển sang `SCHEDULED`.
4. Đến lịch thì chuyển `RUNNING`.
5. Gọi NiFi hoặc trigger flow tương ứng.
6. Ghi `COMPLETED` hoặc `FAILED`.
7. Cập nhật `started_at`, `completed_at`, `failure_reason`.

Việc này không nên chạy đồng bộ trong request HTTP vì download có thể kéo dài.

## 13. Khóa các API NiFi kỹ thuật

Các API start/stop, scheduling và properties hiện đang nằm trong [call_api.py](<./src/web/backend/test/call_api.py>). Nếu sau này chuyển chúng vào ứng dụng thật, phải giới hạn cho Data Engineer:

```python
Depends(require_roles(UserRole.DATA_ENGINEER))
```

RF Engineer không được:

- Start/stop processor.
- Sửa scheduling.
- Sửa properties.
- Thay đổi concurrent tasks.
- Xem allocation history toàn hệ thống.

## Cấu trúc backend đề xuất

```text
backend/
├── models/
│   ├── user.py
│   ├── nifi_source.py
│   ├── download_request.py
│   └── metric_history.py
├── schemas/
│   ├── auth_schemas.py
│   ├── source_schemas.py
│   ├── download_request_schemas.py
│   └── dashboard_schemas.py
├── services/
│   ├── auth_service.py
│   ├── source_service.py
│   ├── availability_service.py
│   ├── download_request_service.py
│   └── dashboard_service.py
├── controllers/
│   ├── auth_controller.py
│   ├── source_controller.py
│   ├── download_request_controller.py
│   └── dashboard_controller.py
├── dependencies/
│   └── auth_dependencies.py
└── routes/
    ├── auth_route.py
    ├── source_route.py
    ├── download_request_route.py
    └── dashboard_route.py
```

Thứ tự nên triển khai:

1. ORM model và migration.
2. `/auth/me` và bảo vệ role.
3. `GET /radio/sources`.
4. `POST /radio/download-requests`.
5. My Requests và Request Detail.
6. Download History.
7. Dashboard aggregate.
8. Availability/recommendation.
9. Worker cập nhật trạng thái request.
10. Unit test và integration test.

> Bỏ phần recommendation nhé.

<details><summary>2 previous messages</summary>

> Mình sẽ loại recommendation khỏi phạm vi RF Engineer: bỏ bước đánh giá/gợi ý thời gian, các trường recommendation trong request detail/dashboard và ưu tiên triển khai. Mình kiểm tra hai bản tài liệu đang mở để cập nhật nhất quán, không đụng vào code backend.
>
> Mình đã bỏ toàn bộ khối recommendation khỏi cả hai bản tài liệu, đồng thời giữ lại bước kiểm tra availability vì đây vẫn là yêu cầu độc lập: frontend cần biết source có sẵn sàng hay đang bận trước khi submit. Mình đang rà lại các tham chiếu còn sót và thứ tự tiêu đề.
</details>

Đã bỏ toàn bộ phần recommendation khỏi cả hai tài liệu:

- [rf_engineer_ui_requirements.md](<./rf_engineer_ui_requirements.md>)
- [bản trong .codex](<./.codex/skills/dashboard/rf_engineer_ui_requirements.md>)

Đã loại bỏ:

- Mục tiêu nhận gợi ý.
- Khối giao diện System Recommendation.
- Recommendation trong chi tiết request.
- Bước “Show recommendation”.
- Hạng mục recommendation trong thứ tự triển khai.

Phần kiểm tra source availability vẫn được giữ lại. Backend không cần các trường hay endpoint về recommendation nữa.

> Thiết kế lại cho tôi thứ tự triển khai.

<details><summary>2 previous messages</summary>

> Mình sẽ sắp lại roadmap theo dependency kỹ thuật thay vì theo thứ tự màn hình: nền tảng dữ liệu và phân quyền trước, API nghiệp vụ sau, dashboard cuối vì nó tổng hợp từ các phần còn lại. Mình kiểm tra các model bạn vừa tạo và tài liệu “Các bước phát triển” để roadmap bám đúng trạng thái code hiện tại.
>
> Hiện ba model nghiệp vụ mới vẫn chưa hoàn thiện (`download_request.py` và `nifi_source.py` trống, `metric_history.py` mới có import và `class` chưa hợp lệ), nên bắt đầu bằng Dashboard sẽ bị phụ thuộc ngược và phải làm mock nhiều. Roadmap mới sẽ bắt đầu từ contract/database → auth → source → request lifecycle → history → dashboard → kiểm thử/tích hợp. Bản tài liệu ở thư mục gốc hiện không tồn tại trên filesystem dù IDE vẫn đang mở, nên mình sẽ kiểm tra lại trước khi cập nhật để không ghi đè một buffer chưa lưu.
</details>

Đã thiết kế lại thứ tự triển khai trong [rf_engineer_ui_requirements.md](<./.codex/skills/dashboard/rf_engineer_ui_requirements.md:285>) thành 9 giai đoạn:

1. Nền tảng dữ liệu và ORM.
2. Xác thực, phân quyền.
3. Danh mục và trạng thái source.
4. Tạo download request.
5. My Requests và Request Detail.
6. Worker/Airflow xử lý vòng đời request.
7. Download History.
8. Dashboard tổng hợp.
9. Kiểm thử và tích hợp frontend.

Dashboard được chuyển xuống gần cuối vì phụ thuộc dữ liệu từ source, request và history.

Lưu ý: file `project/rf_engineer_ui_requirements.md` đang mở trong IDE nhưng hiện không tồn tại trên filesystem, có thể là buffer chưa lưu. Vì vậy mình chỉ cập nhật bản trong `.codex`, tránh ghi đè nội dung chưa lưu. Ngoài ra, bạn nên bắt đầu từ giai đoạn 1 vì `download_request.py` và `nifi_source.py` đang trống, còn `metric_history.py` có khai báo `class` chưa hoàn chỉnh.

> ok vậy để thực hiện 4 giai đoạn đầu. Tôi cần code những gì. Lưu ý là k cần code hộ

<details><summary>1 previous message</summary>

> Mình sẽ biến 4 giai đoạn đầu thành checklist code cụ thể theo từng file, gồm model/schema/service/controller/route, migration, API contract và điều kiện hoàn thành. Mình chỉ hướng dẫn; không sửa file. Trước hết mình đọc `task 1.md` và trạng thái code hiện tại để tránh yêu cầu bạn làm lại phần đã có.
</details>

Để hoàn thành 4 giai đoạn đầu, bạn nên code theo thứ tự dưới đây. Không cần làm Dashboard, History, worker hay recommendation ở thời điểm này.

## Giai đoạn 1 — Nền tảng dữ liệu và ORM

### 1.1. Tạo enum dùng chung

Nên tạo:

```text
backend/constants/enums.py
```

Chứa:

- `UserRole`
- `DownloadRequestStatus`
- `SourceAvailability`

Giá trị cần có:

```text
UserRole:
- Data Engineer
- Radio Frequency Engineer

DownloadRequestStatus:
- PENDING
- SCHEDULED
- RUNNING
- COMPLETED
- FAILED
- REJECTED

SourceAvailability:
- AVAILABLE
- BUSY
- HIGH_LOAD
- UNAVAILABLE
```

Không nên để `UserRole` trong `auth_schemas.py` rồi import ngược vào model như hiện tại. Model phụ thuộc schema dễ gây phụ thuộc vòng. Cả model, schema và service nên import enum từ module dùng chung.

### 1.2. Hoàn thiện `NifiSource` model

File:

```text
backend/models/nifi_source.py
```

Cần ánh xạ các trường:

| Thuộc tính ORM | Cột database |
|---|---|
| `id` | `id` |
| `external_source_id` | `source_id` |
| `name` | `source_name` |
| `process_group_id` | `process_group_id` |
| `vendor` | `vendor` |
| `remote_path` | `remote_path` |
| `schedule_start` | `schedule_start` |
| `schedule_end` | `schedule_end` |
| `status` | `status` |

Nên đổi tên thuộc tính Python thành `external_source_id` để không nhầm với khóa chính `id`.

Relationships cần có:

```text
NifiSource.metric_history
NifiSource.download_requests
```

### 1.3. Hoàn thiện `MetricHistory`

File [metric_history.py](<./src/web/backend/models/metric_history.py>) hiện có dòng `class` chưa hoàn chỉnh.

Model cần:

- Composite primary key: `source_id` và `recorded_at`.
- Foreign key tới `nifi_source.id`.
- Các trường metric đúng kiểu:
  - `BigInteger`: queue count, queue bytes.
  - `Float`: các rate.
  - `Integer`: concurrent tasks.
  - `DateTime(timezone=True)`: recorded time.
- Relationship `source`.

### 1.4. Hoàn thiện `DownloadRequest`

File:

```text
backend/models/download_request.py
```

Các trường:

```text
id
user_id
source_id
start_time
end_time
status
created_at
started_at
completed_at
failure_reason
```

Relationships:

```text
DownloadRequest.user
DownloadRequest.source
```

Thiết lập mặc định:

```text
status = PENDING
created_at = thời gian database
```

Các trường `created_at` và `status` nên `NOT NULL`.

### 1.5. Bổ sung relationship cho `User`

Trong `models/user.py`, thêm relationship:

```text
User.download_requests
```

Quan hệ tổng thể:

```text
User 1 ─── N DownloadRequest N ─── 1 NifiSource
                                      │
                                      1
                                      │
                                      N
                                MetricHistory
```

### 1.6. Sửa database schema

Trong `table.sql` hoặc migration cần:

- Thống nhất `process_group_id` thành `BIGINT`, vì nó tham chiếu `BIGSERIAL`.
- Dùng `TIMESTAMPTZ` cho các thời điểm.
- Thêm default `PENDING`.
- Thêm default `CURRENT_TIMESTAMP`.
- Thêm check constraint cho role và request status.
- Thêm index phục vụ truy vấn.

Các index quan trọng:

```text
download_request(user_id, created_at)
download_request(user_id, status)
download_request(source_id, status)
metric_history(source_id, recorded_at DESC)
```

Nếu database đã tồn tại, không sửa mỗi `table.sql`; cần tạo migration mới. Có thể dùng Alembic hoặc SQL migration được đánh số.

### Kết quả giai đoạn 1

Bạn phải chạy được các kiểm tra:

- Import tất cả model không lỗi.
- Query danh sách source.
- Query metric mới nhất của một source.
- Tạo thử một download request bằng ORM.
- Relationships trả đúng user và source.
- Giá trị status sai bị database từ chối.

---

## Giai đoạn 2 — Xác thực và phân quyền

### 2.1. Hoàn thiện `/auth/me`

Bổ sung schema:

```text
CurrentUserResponse
- user_id
- username
- role
```

Endpoint:

```http
GET /auth/me
Authorization: Bearer <access_token>
```

Frontend cần endpoint này để khôi phục thông tin đăng nhập và xác định giao diện theo role.

### 2.2. Hoàn thiện dependency xác thực

Trong `auth_dependencies.py`:

- Đọc Bearer token.
- Decode JWT.
- Validate claim `sub`.
- Chuyển `sub` thành số nguyên.
- Query lại user từ database.
- Trả `401` nếu token sai, hết hạn hoặc user không tồn tại.
- Sử dụng role hiện tại từ database.

Nên đặt `get_current_user()` trước `require_roles()` để code dễ đọc hơn.

### 2.3. Bảo vệ toàn bộ router RF

Tạo router:

```text
backend/routes/radio_route.py
```

Prefix:

```text
/radio
```

Có thể áp dụng role cho cả router:

```text
Radio Frequency Engineer
```

Tuy nhiên, các endpoint cần biết `current_user.id` vẫn phải inject `get_current_user()` trực tiếp.

Quy tắc HTTP:

| Trường hợp | Status |
|---|---:|
| Không có token | 401 |
| Token sai/hết hạn | 401 |
| Đúng token nhưng sai role | 403 |
| Đúng role | Cho phép |

### 2.4. Xóa endpoint phân quyền thử nghiệm

Sau khi test xong, nên bỏ:

```text
POST /auth/data-engineer
POST /auth/rf-egineer
GET /auth/shared-resource
```

Đây chỉ là endpoint thử nghiệm, không phải API nghiệp vụ. Ngoài ra `/rf-egineer` đang sai chính tả.

### 2.5. Cân nhắc quyền tự chọn role khi signup

Hiện người dùng được tự gửi role trong signup. Nếu hai role có quyền khác nhau, việc này cho phép người dùng tự cấp quyền Data Engineer.

Bạn cần chọn một trong hai chính sách:

- Signup công khai luôn tạo `Radio Frequency Engineer`.
- Role chỉ được quản trị viên thay đổi.
- Hoặc cho chọn role nếu đây chỉ là hệ thống demo.

### Kết quả giai đoạn 2

Test đủ:

```text
GET /auth/me không token       → 401
GET /auth/me token sai         → 401
GET /radio/sources sai role    → 403
GET /radio/sources đúng role   → không bị chặn
```

---

## Giai đoạn 3 — Danh mục và trạng thái source

### 3.1. Tạo schema source

File:

```text
backend/schemas/source_schemas.py
```

Cần ít nhất:

```text
SourceListItem
SourceDetailResponse
SourceAvailabilityResponse
```

Thông tin dành cho RF Engineer:

```text
id
source_code
source_name
vendor
availability
load_level
accepting_requests
last_metric_at
```

Không cần trả:

- `concurrent_tasks`
- Chi tiết queue byte.
- NiFi processor ID.
- Cấu hình processor.
- Allocation nội bộ.

### 3.2. Tạo `SourceService`

File:

```text
backend/services/source_service.py
```

Các method cần có:

```text
list_sources()
get_source_by_id()
get_latest_metric()
calculate_availability()
```

`get_latest_metric()` phải lấy bản ghi có `recorded_at` mới nhất của từng source, tránh query một lần cho mỗi source gây lỗi N+1.

### 3.3. Quy định cách tính availability

Bạn cần xác định rõ rule, ví dụ:

```text
Source status không hoạt động
    → UNAVAILABLE

Không có metric hoặc metric quá cũ
    → UNAVAILABLE

Queue vượt ngưỡng cao
    → HIGH_LOAD

Queue vượt ngưỡng trung bình
    → BUSY

Còn lại
    → AVAILABLE
```

Đưa ngưỡng vào config thay vì viết rải rác trong service:

```text
METRIC_STALE_MINUTES
BUSY_QUEUE_COUNT
HIGH_LOAD_QUEUE_COUNT
```

### 3.4. Tạo controller và route

Các file:

```text
backend/controllers/source_controller.py
backend/routes/source_route.py
```

API:

```http
GET /radio/sources
GET /radio/sources/{source_id}
GET /radio/sources/{source_id}/availability
```

Endpoint danh sách có thể hỗ trợ:

```text
?q=ENM
&vendor=Ericsson
&availability=AVAILABLE
```

`availability` chỉ trả trạng thái hiện tại. Không nhận khoảng thời gian và không sinh recommendation.

### 3.5. Đăng ký router

Trong `main.py`:

```text
include source router
```

### Kết quả giai đoạn 3

- Lấy được danh sách source.
- Lấy được chi tiết source.
- Source không tồn tại trả `404`.
- Metric quá cũ không được coi là available.
- Sai role trả `403`.
- Response không làm lộ thông tin vận hành NiFi.

---

## Giai đoạn 4 — Tạo download request

### 4.1. Tạo schema request

File:

```text
backend/schemas/download_request_schemas.py
```

`CreateDownloadRequest` chỉ nhận:

```text
source_id
start_time
end_time
```

Không nhận:

```text
user_id
status
created_at
failure_reason
```

Các trường trên phải do backend quản lý.

Response nên có:

```text
id
source
start_time
end_time
status
created_at
```

### 4.2. Validate input

Trong Pydantic schema hoặc service:

- `start_time < end_time`.
- Bắt buộc timezone.
- Giới hạn độ dài khoảng dữ liệu nếu nghiệp vụ cần.
- Source ID phải hợp lệ.
- Không cho khoảng thời gian vô nghĩa.
- Có thể ngăn request trùng source và khoảng thời gian của cùng user.

Validation liên quan database phải đặt trong service, không đặt trong Pydantic validator.

### 4.3. Tạo `DownloadRequestService`

File:

```text
backend/services/download_request_service.py
```

Method chính:

```text
create_request(db, current_user, payload)
```

Trình tự:

```text
1. Tìm source.
2. Không thấy source → 404.
3. Kiểm tra source availability.
4. Không thể tiếp nhận → 409.
5. Kiểm tra request trùng.
6. Lấy user_id từ current_user.id.
7. Tạo request với PENDING.
8. Commit.
9. Refresh.
10. Trả response.
```

Nếu commit lỗi:

```text
rollback transaction
```

Không tin `availability` do frontend gửi lên. Backend phải kiểm tra lại ngay lúc tạo để tránh trạng thái source thay đổi giữa hai request HTTP.

### 4.4. Tạo controller và route

Các file:

```text
backend/controllers/download_request_controller.py
backend/routes/download_request_route.py
```

Endpoint:

```http
POST /radio/download-requests
```

Nên trả:

```text
201 Created
```

Ví dụ request:

```json
{
  "source_id": 6,
  "start_time": "2026-09-14T10:00:00+07:00",
  "end_time": "2026-09-14T12:00:00+07:00"
}
```

Ví dụ response:

```json
{
  "id": 105,
  "source": {
    "id": 6,
    "name": "ENM06"
  },
  "start_time": "2026-09-14T10:00:00+07:00",
  "end_time": "2026-09-14T12:00:00+07:00",
  "status": "PENDING",
  "created_at": "2026-09-14T09:45:00+07:00"
}
```

### 4.5. Chưa gọi NiFi trong endpoint này

Ở giai đoạn 4, API chỉ cần:

```text
Validate → lưu PENDING → trả 201
```

Không nên giữ HTTP request để đợi NiFi download. Việc lấy request `PENDING` và thực thi thuộc giai đoạn worker/Airflow sau này.

## Danh sách file cuối cùng cần có

```text
backend/
├── constants/
│   └── enums.py
├── models/
│   ├── user.py
│   ├── nifi_source.py
│   ├── metric_history.py
│   └── download_request.py
├── schemas/
│   ├── auth_schemas.py
│   ├── source_schemas.py
│   └── download_request_schemas.py
├── services/
│   ├── auth_service.py
│   ├── source_service.py
│   └── download_request_service.py
├── controllers/
│   ├── auth_controller.py
│   ├── source_controller.py
│   └── download_request_controller.py
├── routes/
│   ├── auth_route.py
│   ├── source_route.py
│   └── download_request_route.py
└── dependencies/
    └── auth_dependencies.py
```

Thứ tự code cụ thể nên là:

```text
Enums
→ ORM models
→ Database migration
→ Test ORM
→ /auth/me
→ Role protection
→ Source schemas/service/API
→ Availability rule
→ Download request schemas/service/API
→ Integration tests
```

Hoàn thành bốn giai đoạn nghĩa là frontend đã có thể đăng nhập, xác định role, tải danh sách source, xem availability và tạo một download request `PENDING` hợp lệ.

> Tại sao trong models bạn không có  nifi\_component và nifi\_process\_group ?

Mình không liệt kê hai model đó vì roadmap trước được thu hẹp cho 4 giai đoạn của giao diện RF Engineer. Tuy nhiên, nếu mục tiêu giai đoạn 1 là ánh xạ đầy đủ database bằng ORM thì việc bỏ `nifi_process_group` là chưa hợp lý, còn `nifi_component` nên có model nhưng không cần expose cho RF Engineer.

## `NifiProcessGroup` — nên có

Bảng `nifi_source` chứa:

```sql
process_group_id INTEGER NOT NULL
REFERENCES nifi_process_group(id)
```

Do đó nên tạo:

```text
backend/models/nifi_process_group.py
```

Model cần ánh xạ:

```text
id
group_id
group_name
parent_id
level
created_at
updated_at
```

Relationships:

```text
NifiProcessGroup.parent
NifiProcessGroup.children
NifiProcessGroup.sources
```

Đây là quan hệ cây tự tham chiếu:

```text
Process Group cha
├── Process Group con
│   ├── Source A
│   └── Source B
└── Source C
```

Trong `NifiSource` cần relationship ngược:

```text
NifiSource.process_group
```

Nếu không khai báo model này, bạn vẫn có thể query bảng `nifi_source` khi database đã được tạo sẵn. Nhưng `Base.metadata.create_all()` hoặc migration dựa trên SQLAlchemy metadata có thể gặp `NoReferencedTableError` vì không biết bảng đích của foreign key.

## `NifiComponent` — nên có ở data layer

Tạo:

```text
backend/models/nifi_component.py
```

Model ánh xạ:

```text
id
source_id
component_id
component_name
component_type
processor_type
source_component_id
destination_component_id
concurrent_tasks
status
created_at
updated_at
```

Relationships:

```text
NifiComponent.source
NifiSource.components
```

`NifiComponent` cần thiết cho:

- Data Engineer quản lý processor.
- Theo dõi trạng thái component.
- Start/stop processor.
- Thay đổi `concurrent_tasks`.
- Cấu hình NiFi.
- Xác định source có component lỗi hoặc ngừng hoạt động hay không.

## Vì sao RF Engineer không cần API component?

Model tồn tại trong data layer không đồng nghĩa RF Engineer được truy cập nó.

Bạn vẫn tạo đầy đủ model:

```text
NifiProcessGroup
NifiSource
NifiComponent
MetricHistory
DownloadRequest
User
```

Nhưng API `/radio/*` chỉ trả dữ liệu đã tổng hợp:

```json
{
  "source_name": "ENM06",
  "availability": "AVAILABLE",
  "load_level": "MODERATE"
}
```

Không trả:

```text
processor_id
processor_type
concurrent_tasks
component configuration
connection internals
```

Các endpoint thao tác `NifiComponent` chỉ dành cho Data Engineer:

```text
GET  /data-engineer/components
PUT  /data-engineer/components/{id}/scheduling
PUT  /data-engineer/components/{id}/properties
POST /data-engineer/components/{id}/start
POST /data-engineer/components/{id}/stop
```

## Danh sách model đúng cho giai đoạn 1

```text
backend/models/
├── user.py
├── nifi_process_group.py
├── nifi_source.py
├── nifi_component.py
├── metric_history.py
└── download_request.py
```

Quan hệ tổng thể:

```text
NifiProcessGroup
├── children: NifiProcessGroup[]
└── sources: NifiSource[]
       ├── components: NifiComponent[]
       ├── metrics: MetricHistory[]
       └── download_requests: DownloadRequest[]
                                    └── user: User
```

Ngoài ra, trong SQL hiện tại `nifi_process_group.id` là `BIGSERIAL` nhưng `nifi_source.process_group_id` là `INTEGER`. Bạn nên đổi foreign key đó thành `BIGINT` để đồng nhất kiểu dữ liệu.

Tóm lại: hai model này nên tồn tại để ORM phản ánh đúng database. Chúng bị thiếu trong danh sách trước vì mình đang giới hạn theo chức năng RF Engineer; điều nên giới hạn là API và response của RF Engineer, không phải các model nền tảng.

> Giai đoạn 2 thực hiện kiểu gì ?

<details><summary>2 previous messages</summary>

> Mình sẽ hướng dẫn Giai đoạn 2 theo đúng code hiện tại: hoàn thiện nhận diện user từ JWT, endpoint `/auth/me`, áp quyền ở cấp router và kiểm thử 401/403. Mình chỉ đọc và chỉ ra từng việc cần tự code, không sửa file.
>
> Lệnh đọc vừa bị lỗi cú pháp nội bộ và chưa thu được dữ liệu. Mình chạy lại bằng lệnh tối giản.
</details>

Giai đoạn 2 gồm hai phần khác nhau:

- Authentication: người gọi API là ai?
- Authorization: người đó có role nào và được phép làm gì?

Code hiện tại đã có nền tảng nhưng cần hoàn thiện theo thứ tự sau.

## 1. Sửa lại vị trí import `UserRole`

Bạn đã chuyển `UserRole` sang:

```text
backend/constants/enums.py
```

Nhưng một số file vẫn import gián tiếp từ `auth_schemas.py`:

- [user.py](<./src/web/backend/models/user.py>)
- [auth_service.py](<./src/web/backend/services/auth_service.py>)
- [auth_dependencies.py](<./src/web/backend/dependencies/auth_dependencies.py>)
- [auth_route.py](<./src/web/backend/routes/auth_route.py>)

Tất cả nên import trực tiếp:

```python
from backend.constants.enums import UserRole
```

Quy tắc dependency nên là:

```text
constants ← models
constants ← schemas
models + schemas ← services
services ← controllers
controllers ← routes
```

Model không nên import schema.

## 2. Chuẩn hóa dữ liệu role trong database

Database chỉ nên chứa đúng:

```text
Data Engineer
Radio Frequency Engineer
```

Kiểm tra:

```sql
SELECT DISTINCT role FROM users;
```

Nếu vẫn có tài khoản cũ với role `"Engineer"`, cần migration chuyển chúng sang role hợp lệ.

Sau đó thêm:

- Default role nếu cần.
- Check constraint giới hạn hai role.
- `NOT NULL`.

Nếu không làm bước này, `require_roles()` có thể từ chối các tài khoản cũ dù token vẫn hợp lệ.

## 3. Hoàn thiện schema người dùng hiện tại

Trong `auth_schemas.py`, thêm schema dành cho `/auth/me`:

```text
CurrentUserResponse
├── user_id
├── username
└── role
```

Vì model sử dụng thuộc tính Python `id` nhưng API trả `user_id`, dùng cùng cách alias như `SignUpResponse`.

Schema phải bật `from_attributes` để đọc được SQLAlchemy object.

Không trả về:

```text
hashed_password
```

## 4. Hoàn thiện `get_current_user()`

Trong [auth_dependencies.py](<./src/web/backend/dependencies/auth_dependencies.py>), nên đặt `get_current_user()` trước `require_roles()`.

Luồng xử lý:

```text
Authorization header
        ↓
Kiểm tra Bearer token
        ↓
Decode và verify JWT
        ↓
Lấy claim sub
        ↓
Chuyển sub thành user_id
        ↓
Query user trong database
        ↓
Trả về User hiện tại
```

Các trường hợp lỗi:

| Trường hợp | Kết quả |
|---|---:|
| Không có Authorization header | 401 |
| Không dùng Bearer | 401 |
| JWT sai chữ ký | 401 |
| JWT hết hạn | 401 |
| Thiếu `sub` | 401 |
| `sub` không phải số | 401 |
| User đã bị xóa | 401 |

Response `401` nên có:

```http
WWW-Authenticate: Bearer
```

Hiện `decode_access_token()` đã bắt `JWTError`, nên token hết hạn cũng sẽ được coi là không hợp lệ.

## 5. Không nên tin role trong JWT để cấp quyền

Token hiện chứa:

```json
{
  "sub": "12",
  "username": "example",
  "role": "Radio Frequency Engineer"
}
```

Việc chứa role trong token hữu ích cho frontend, nhưng backend nên dùng:

```text
current_user.role lấy từ database
```

`get_current_user()` của bạn hiện đã query lại user, đây là hướng đúng.

Ví dụ admin đổi role trong database:

```text
Radio Frequency Engineer → Data Engineer
```

Backend áp dụng role mới ngay, không cần chờ JWT cũ hết hạn.

## 6. Hoàn thiện `require_roles()`

Dependency này nhận danh sách role được phép:

```text
require_roles(Data Engineer)
require_roles(Radio Frequency Engineer)
require_roles(Data Engineer, Radio Frequency Engineer)
```

Luồng xử lý:

```text
get_current_user()
       ↓
Lấy current_user.role
       ↓
So sánh với allowed_roles
       ↓
Cho phép hoặc trả 403
```

Phân biệt chính xác:

- `401`: chưa xác thực được danh tính.
- `403`: đã xác thực nhưng không đủ quyền.

Nên thêm kiểm tra trường hợp role trong database không thuộc enum hợp lệ. Có thể trả `403` thay vì làm ứng dụng lỗi 500.

## 7. Tạo endpoint `/auth/me`

Trong `auth_route.py`:

```http
GET /auth/me
```

Endpoint:

- Dùng `Depends(get_current_user)`.
- Trả SQLAlchemy `User`.
- Dùng `CurrentUserResponse` làm `response_model`.

Response:

```json
{
  "user_id": 12,
  "username": "rf_user",
  "role": "Radio Frequency Engineer"
}
```

Endpoint này phục vụ frontend:

1. Frontend lấy token đã lưu.
2. Gọi `/auth/me`.
3. Nhận role.
4. Điều hướng đến `/radio/dashboard` hoặc giao diện Data Engineer.
5. Nếu nhận `401`, xóa token và chuyển về trang login.

## 8. Tách các endpoint thử nghiệm khỏi auth route

Các endpoint hiện tại:

```text
POST /auth/data-engineer
POST /auth/rf-egineer
GET /auth/shared-resource
```

chỉ nên dùng để test dependency. Sau khi kiểm tra xong, hãy xóa chúng.

Ngoài ra `rf-egineer` đang viết sai chính tả.

`auth_route.py` chỉ nên chịu trách nhiệm:

```text
POST /auth/signup
POST /auth/login
GET  /auth/me
```

## 9. Tạo router riêng cho RF Engineer

Tạo:

```text
backend/routes/radio_route.py
```

Router sử dụng prefix:

```text
/radio
```

Có hai cách bảo vệ.

### Bảo vệ toàn bộ router

Áp dụng dependency role ngay khi khai báo router. Khi đó mọi endpoint trong router đều yêu cầu role RF Engineer.

Phù hợp khi tất cả endpoint dưới `/radio/*` chỉ dành cho RF Engineer.

### Bảo vệ từng endpoint

Mỗi endpoint tự khai báo `require_roles()`.

Phù hợp khi một router chứa API dùng chung cho nhiều role.

Với kiến trúc hiện tại, nên bảo vệ toàn bộ router `/radio`, sau đó vẫn inject `get_current_user()` vào endpoint cần `current_user.id`.

Ví dụ:

```text
GET  /radio/sources
GET  /radio/sources/{id}
POST /radio/download-requests
```

đều bị chặn nếu user không phải Radio Frequency Engineer.

## 10. Bảo vệ Data Engineer API riêng

Sau này tạo:

```text
backend/routes/data_engineer_route.py
```

Prefix:

```text
/data-engineer
```

Các API vận hành NiFi phải yêu cầu role Data Engineer:

```text
start/stop processor
thay đổi scheduling
thay đổi properties
thay đổi concurrent tasks
xem allocation
```

Ẩn nút trên frontend là chưa đủ; backend bắt buộc phải trả `403` khi RF Engineer gọi trực tiếp.

## 11. Đăng ký router trong `main.py`

Sau khi tạo router RF, đăng ký nó vào FastAPI app.

Kết quả Swagger phải có các nhóm:

```text
Authentication
Radio Engineer
Data Engineer
Health
```

Endpoint `/radio/*` phải hiển thị yêu cầu HTTP Bearer authentication.

## 12. Quyết định chính sách signup

Hiện request signup cho phép client gửi:

```json
{
  "role": "Data Engineer"
}
```

Điều này nghĩa là bất kỳ ai cũng có thể tự tạo tài khoản Data Engineer.

Bạn cần chọn rõ một chính sách.

### Nếu đây là hệ thống demo

Có thể giữ việc tự chọn role.

### Nếu đây là hệ thống thực tế

Signup công khai nên:

- Không nhận role.
- Tự gán `Radio Frequency Engineer`.
- Chỉ admin hoặc thao tác trực tiếp trong database được nâng lên `Data Engineer`.

Đây là phần bảo mật quan trọng nhất của giai đoạn 2.

## 13. Chuẩn hóa login

Signup đã chuyển username về chữ thường, nhưng `LoginRequest` chưa chắc thực hiện tương tự.

Nên bảo đảm:

```text
signup "User01" → lưu "user01"
login  "User01" → query "user01"
```

Nếu không, người dùng đăng nhập bằng chữ hoa có thể thất bại.

Ngoài ra nên dùng cùng một thông báo cho:

- Username không tồn tại.
- Password không đúng.

Tránh tiết lộ tài khoản nào đang tồn tại.

## 14. Viết test cho Giai đoạn 2

Bạn nên có các nhóm test sau.

### Authentication

| Test | Mong đợi |
|---|---:|
| Login đúng | 200 |
| Sai password | 401 |
| User không tồn tại | 401 |
| Token hết hạn | 401 |
| Token bị sửa | 401 |
| `/auth/me` không token | 401 |
| `/auth/me` token đúng | 200 |

### Authorization

Tạo hai user:

```text
data_user → Data Engineer
rf_user   → Radio Frequency Engineer
```

Kiểm tra:

| Endpoint | Data user | RF user |
|---|---:|---:|
| `/radio/test` | 403 | 200 |
| `/data-engineer/test` | 200 | 403 |
| Endpoint chung | 200 | 200 |

### Kiểm tra database là nguồn quyền

1. Login bằng RF Engineer và lấy token.
2. Đổi role trong database thành Data Engineer.
3. Gọi lại `/radio/test` bằng token cũ.
4. Kết quả phải là `403`.

Test này xác nhận backend dùng role từ database, không tin role cũ trong JWT.

## Thứ tự code cụ thể

Bạn có thể làm lần lượt:

1. Sửa toàn bộ import `UserRole`.
2. Migration làm sạch role cũ.
3. Tạo `CurrentUserResponse`.
4. Hoàn thiện `get_current_user()`.
5. Hoàn thiện `require_roles()`.
6. Tạo `GET /auth/me`.
7. Tạo `radio_route.py`.
8. Áp role RF cho toàn router.
9. Tạo router Data Engineer rỗng hoặc endpoint test tạm.
10. Đăng ký router trong `main.py`.
11. Kiểm tra chính sách signup.
12. Viết test 401/403.
13. Xóa các endpoint thử nghiệm trong `auth_route.py`.

Giai đoạn 2 được coi là hoàn thành khi backend luôn trả đúng: chưa đăng nhập → `401`, sai role → `403`, đúng role → thành công; đồng thời không có cách gọi trực tiếp API NiFi bằng tài khoản RF Engineer.

> METRIC\_STALE\_MINUTES
> BUSY\_QUEUE\_COUNT
> HIGH\_LOAD\_QUEUE\_COUNT
>
> Các chỉ số này có nghĩa là gì ?

Ba giá trị này là các ngưỡng cấu hình để backend chuyển metric kỹ thuật của NiFi thành trạng thái dễ hiểu cho người dùng:

```text
AVAILABLE
BUSY
HIGH_LOAD
UNAVAILABLE
```

## `METRIC_STALE_MINUTES`

Số phút tối đa mà một bản ghi metric còn được coi là mới và đáng tin cậy.

Ví dụ:

```python
METRIC_STALE_MINUTES = 5
```

Nếu thời điểm hiện tại là `10:10`:

- Metric ghi lúc `10:08` → còn hiệu lực.
- Metric ghi lúc `09:55` → đã quá cũ.

Cách kiểm tra:

```text
now - recorded_at > METRIC_STALE_MINUTES
```

Metric quá cũ thường nên khiến source có trạng thái:

```text
UNAVAILABLE
```

hoặc `UNKNOWN` nếu bạn bổ sung trạng thái này.

Ý nghĩa: backend không nên thông báo source đang rảnh dựa trên dữ liệu đã lâu không được cập nhật.

---

## `BUSY_QUEUE_COUNT`

Số lượng FlowFile đang chờ trong queue mà từ đó source bắt đầu được coi là bận.

Ví dụ:

```python
BUSY_QUEUE_COUNT = 10_000
```

Nếu:

```text
queued_count >= 10.000
```

thì source chuyển từ:

```text
AVAILABLE → BUSY
```

Source vẫn có thể tiếp nhận download request, nhưng tốc độ xử lý có thể chậm hơn.

---

## `HIGH_LOAD_QUEUE_COUNT`

Số lượng FlowFile trong queue mà từ đó source được coi là đang có tải cao.

Ví dụ:

```python
HIGH_LOAD_QUEUE_COUNT = 50_000
```

Nếu:

```text
queued_count >= 50.000
```

thì source có trạng thái:

```text
HIGH_LOAD
```

Tùy quy tắc nghiệp vụ, trạng thái này có thể:

- Vẫn cho phép tạo request nhưng cảnh báo người dùng.
- Hoặc từ chối request mới bằng `409 Conflict`.

Luôn phải đảm bảo:

```python
BUSY_QUEUE_COUNT < HIGH_LOAD_QUEUE_COUNT
```

## Ví dụ quy tắc tổng hợp

Với cấu hình:

```python
METRIC_STALE_MINUTES = 5
BUSY_QUEUE_COUNT = 10_000
HIGH_LOAD_QUEUE_COUNT = 50_000
```

Có thể phân loại:

| Điều kiện | Trạng thái |
|---|---|
| Source bị stop | `UNAVAILABLE` |
| Không có metric | `UNAVAILABLE` |
| Metric cũ hơn 5 phút | `UNAVAILABLE` |
| `queued_count >= 50.000` | `HIGH_LOAD` |
| `queued_count >= 10.000` | `BUSY` |
| `queued_count < 10.000` | `AVAILABLE` |

Thứ tự kiểm tra rất quan trọng: kiểm tra `HIGH_LOAD` trước `BUSY`, vì `60.000` đồng thời lớn hơn cả hai ngưỡng.

## Đây chưa phải các con số cố định

Các giá trị `5`, `10.000` và `50.000` chỉ là ví dụ. Ngưỡng thực tế nên được xác định từ dữ liệu vận hành:

- Chu kỳ thu thập metric.
- Tốc độ xử lý trung bình.
- Kích thước file trung bình.
- Backpressure threshold của NiFi.
- Khả năng xử lý của từng source.
- Phân bố `queued_count` trong `metric_history`.

Nếu metric được thu thập mỗi phút, `METRIC_STALE_MINUTES = 5` tương đối hợp lý. Nếu thu thập mỗi 10 phút thì ngưỡng 5 phút sẽ khiến source thường xuyên bị coi là unavailable.

Ngoài ra, `queued_count` đơn lẻ chưa phản ánh hoàn toàn tải. Sau phiên bản đầu, bạn có thể kết hợp:

```text
queued_count
queue_bytes
input_file_rate
processed_file_rate
```

Ví dụ, nếu tốc độ đầu vào lớn hơn tốc độ xử lý trong thời gian dài:

```text
input_file_rate > processed_file_rate
```

thì queue đang có xu hướng tăng và source có thể sớm quá tải, dù `queued_count` hiện tại chưa chạm ngưỡng.

> Các chỉ số `METRIC_STALE_MINUTES`, BUSY\_QUEUE\_COUNT, HIGH\_LOAD\_QUEUE\_COUNT. Không nên fix cứng ngưỡng như vậy khi chưa có dữ liệu kiểm chứng thực tế là bao nhiêu

Đúng. Khi chưa có dữ liệu vận hành, đặt cố định kiểu:

```python
BUSY_QUEUE_COUNT = 10_000
HIGH_LOAD_QUEUE_COUNT = 50_000
```

chỉ là phỏng đoán và có thể phân loại sai. Mỗi source có lưu lượng, kích thước file và năng lực xử lý khác nhau, nên một ngưỡng chung không phù hợp.

## Nên thiết kế lại

### 1. Freshness dựa trên chu kỳ thu thập metric

Thay vì một số phút tùy ý, dùng:

```text
metric_stale_after = chu kỳ thu thập × số lần cập nhật bị bỏ lỡ
```

Ví dụ hệ thống thu metric mỗi phút và cho phép mất ba lần cập nhật:

```text
stale_after = 1 phút × 3
```

Nên cấu hình:

```python
METRIC_COLLECTION_INTERVAL_SECONDS
MAX_MISSED_METRIC_INTERVALS
```

Nếu chưa biết chu kỳ thu thập thì trả:

```text
UNKNOWN
```

thay vì kết luận `UNAVAILABLE`.

### 2. Dùng backpressure threshold của NiFi

NiFi đã có ngưỡng giới hạn queue theo:

- Số FlowFile.
- Tổng dung lượng queue.

Tính tỷ lệ sử dụng:

```text
object_utilization = queued_count / object_backpressure_threshold
size_utilization = queue_bytes / size_backpressure_threshold

queue_utilization = max(object_utilization, size_utilization)
```

Như vậy `10.000` FlowFile có thể là cao đối với source nhỏ nhưng bình thường với source lớn.

Khi NiFi đã kích hoạt backpressure, có thể xác định source đang `HIGH_LOAD` mà không cần tự đặt một số lượng queue tuyệt đối.

### 3. Dùng dữ liệu lịch sử theo từng source

Sau khi thu thập đủ dữ liệu, tính baseline riêng:

```text
P50: mức tải thông thường
P75: bắt đầu bận
P95: tải cao bất thường
```

Ví dụ:

```text
queued_count < P75       → AVAILABLE
P75 ≤ queued_count < P95 → BUSY
queued_count ≥ P95       → HIGH_LOAD
```

Không nên dùng percentile toàn hệ thống vì ENM01 và ENM06 có thể có quy mô rất khác nhau.

### 4. Kết hợp xu hướng xử lý

Queue hiện tại chưa đủ để kết luận. Nên xét thêm:

```text
input_file_rate
processed_file_rate
queued_count theo thời gian
```

Ví dụ:

```text
input_file_rate > processed_file_rate
và queue liên tục tăng
→ tải đang xấu đi
```

Ngược lại, queue lớn nhưng đang giảm nhanh chưa chắc là `HIGH_LOAD`.

Một chỉ số hữu ích là thời gian dự kiến xử lý hết backlog:

```text
estimated_drain_time =
    queued_count / processed_file_rate
```

## Khi chưa có dữ liệu thì làm gì?

Phiên bản đầu nên dùng trạng thái thận trọng:

```text
NiFi/source không hoạt động → UNAVAILABLE
Metric không có hoặc quá cũ → UNKNOWN
NiFi đang backpressure      → HIGH_LOAD
Các trường hợp còn lại      → AVAILABLE
```

Chưa nên dùng trạng thái `BUSY` dựa trên ngưỡng tự đặt, và đặc biệt không nên từ chối download request chỉ vì một ngưỡng chưa được kiểm chứng.

Sau khi thu thập đủ dữ liệu khoảng 1–4 tuần:

1. Phân tích phân phối metric theo từng source.
2. Đối chiếu thời điểm download chậm hoặc thất bại.
3. Xác định percentile hoặc mô hình load phù hợp.
4. Version hóa cấu hình.
5. Theo dõi false positive/false negative.
6. Điều chỉnh ngưỡng mà không cần sửa code.

Vì vậy, `metric_config.py` hiện tại chỉ nên chứa thông tin có căn cứ như chu kỳ thu thập hoặc cơ chế đọc cấu hình NiFi; chưa nên chứa `BUSY_QUEUE_COUNT` và `HIGH_LOAD_QUEUE_COUNT` dưới dạng các con số giả định.

> Các method như
> list\_sources()
> get\_source\_by\_id()
> get\_latest\_metric()
> calculate\_availability()
>
> Là dữ liệu phải lưu ở database trước rồi đúng không ?. Có 1 vấn đề là hiện tại project chưa có cơ chế đọc RestAPI từ Nifi

Đúng, với kiến trúc DB-first đã đề xuất thì:

- `list_sources()` đọc metadata từ `nifi_source`.
- `get_source_by_id()` đọc một source từ `nifi_source`.
- `get_latest_metric()` đọc metric gần nhất từ `metric_history`.
- `calculate_availability()` tính trạng thái từ source và metric vừa đọc.

Nhưng dữ liệu phải được đồng bộ từ NiFi vào database trước. Nếu hiện chưa có cơ chế gọi NiFi REST API thì `nifi_source`, `nifi_component` và `metric_history` sẽ trống hoặc lỗi thời, khiến các method trên chưa có dữ liệu thật để xử lý.

## Luồng kiến trúc nên có

```text
NiFi REST API
      ↓
NiFi Client
      ↓
Metadata/Metric Collector
      ↓
PostgreSQL + TimescaleDB
      ↓
SourceService
      ↓
GET /radio/sources
```

Không nên để `SourceService.list_sources()` trực tiếp gọi NiFi mỗi khi frontend tải trang.

## 1. Tạo một NiFi API client

Nên tạo:

```text
backend/clients/nifi_client.py
```

Client này chỉ chịu trách nhiệm giao tiếp HTTP với NiFi:

```text
authenticate()
get_process_groups()
get_process_group_status()
get_processors()
get_connections()
get_processor()
```

Nó cần xử lý:

- NiFi URL.
- Username/password hoặc access token.
- Timeout.
- HTTPS certificate.
- Refresh token khi hết hạn.
- HTTP error.
- Parse JSON response.

Các cấu hình đặt trong `nifi_config.py` hoặc `.env`:

```text
NIFI_URL
NIFI_USERNAME
NIFI_PASSWORD
NIFI_ROOT_PROCESS_GROUP_ID
NIFI_VERIFY_SSL
NIFI_REQUEST_TIMEOUT_SECONDS
```

Trong môi trường production không nên mặc định `verify=False`.

## 2. Xác định “source” trong NiFi là đối tượng nào

Trước khi code collector, bạn phải xác định mapping nghiệp vụ:

```text
Một source ENM tương ứng với:
- một Process Group?
- một Processor?
- hay một nhóm Processor và Connection?
```

Ví dụ nếu mỗi ENM là một process group:

```text
NiFi Process Group ENM06
        ↓
nifi_process_group
        ↓
nifi_source: ENM06
        ↓
các processor bên trong
        ↓
nifi_component
```

Cần có quy tắc nhận diện ổn định, chẳng hạn:

- Theo NiFi UUID.
- Theo parameter/context.
- Theo naming convention như `ENM01`, `ENM02`.
- Theo một file cấu hình mapping.

Không nên chỉ dựa vào tên nếu người vận hành có thể đổi tên process group.

## 3. Tạo service đồng bộ metadata

Tạo:

```text
backend/services/nifi_sync_service.py
```

Nhiệm vụ:

1. Gọi NiFi lấy process group.
2. Upsert vào `nifi_process_group`.
3. Xác định source tương ứng.
4. Upsert vào `nifi_source`.
5. Lấy processors/connections.
6. Upsert vào `nifi_component`.
7. Đánh dấu những component không còn xuất hiện nếu cần.

Đồng bộ phải idempotent:

```text
Chạy một lần  → dữ liệu đúng
Chạy lại      → cập nhật dữ liệu, không tạo bản ghi trùng
```

Dùng các ID do NiFi cung cấp làm khóa tự nhiên:

```text
group_id
source_id
component_id
```

## 4. Tạo collector thu thập metric

Tạo một job riêng:

```text
backend/jobs/nifi_metric_collector.py
```

Hoặc tạo Airflow DAG nếu project đã dùng Airflow:

```text
dags/collect_nifi_metrics.py
```

Job chạy định kỳ:

```text
Mỗi N giây/phút
      ↓
Gọi NiFi status API
      ↓
Tổng hợp metric theo source
      ↓
INSERT vào metric_history
```

Dữ liệu cần ghi:

```text
source_id
recorded_at
queued_count
queue_bytes
input_file_rate
input_byte_rate
processed_file_rate
processed_byte_rate
concurrent_tasks
```

Chú ý `metric_history.source_id` nên là khóa chính nội bộ `nifi_source.id`, không phải UUID/string của NiFi.

## 5. Phân biệt metadata sync và metric collection

Hai loại dữ liệu có tần suất khác nhau:

### Metadata

```text
process group
source
processor
component type
vendor
remote path
```

Thay đổi ít, có thể đồng bộ:

```text
5–30 phút/lần
```

### Metric

```text
queued_count
queue_bytes
input rate
processed rate
status
```

Thay đổi liên tục, cần thu thập thường xuyên hơn:

```text
30 giây–5 phút/lần
```

Tần suất cụ thể phải dựa trên nhu cầu giám sát và tải NiFi.

## 6. Sau đó các method hoạt động như thế nào?

### `list_sources()`

Query `nifi_source`, có thể join metric gần nhất:

```text
nifi_source
LEFT JOIN latest metric_history
```

Không query metric riêng từng source vì sẽ tạo N+1 query.

### `get_source_by_id()`

Query source theo khóa chính nội bộ:

```text
NifiSource.id == source_id
```

Không tồn tại thì trả `404`.

### `get_latest_metric()`

Lấy bản ghi mới nhất:

```text
WHERE source_id = ...
ORDER BY recorded_at DESC
LIMIT 1
```

Nếu không có metric, trả `None`.

### `calculate_availability()`

Không cần tự gọi NiFi. Method nhận:

```text
source
latest_metric
current_time
```

và trả trạng thái tổng hợp.

Khi chưa có ngưỡng tải được kiểm chứng, có thể dùng:

```text
Source/processor bị dừng      → UNAVAILABLE
Không có metric              → UNKNOWN
Metric không còn cập nhật    → UNKNOWN
NiFi đang backpressure       → HIGH_LOAD
Hoạt động bình thường        → AVAILABLE
```

Nên bổ sung `UNKNOWN` vào enum. Không có dữ liệu khác với source chắc chắn không hoạt động.

## 7. Không đánh dấu `UNAVAILABLE` khi collector lỗi

Giả sử NiFi đang hoạt động nhưng collector mất kết nối. Khi đó:

```text
NiFi thực tế: hoạt động
Collector: lỗi
Metric: không được cập nhật
```

Backend nên trả:

```text
UNKNOWN
```

không phải `UNAVAILABLE`.

Đồng thời nên lưu trạng thái collector:

```text
last_successful_sync_at
last_sync_error
```

Có thể lưu trong bảng riêng như `integration_sync_state`, hoặc ít nhất ghi log/metric giám sát.

## 8. Có thể gọi NiFi trực tiếp từ API không?

Có thể:

```text
GET /radio/sources
        ↓
SourceService gọi NiFi REST API
        ↓
Trả frontend
```

Nhưng không nên dùng làm kiến trúc chính vì:

- API frontend bị chậm theo NiFi.
- NiFi lỗi thì giao diện lỗi theo.
- Nhiều user gây nhiều request tới NiFi.
- Không có dữ liệu lịch sử.
- Khó tính metric trend.
- Làm lộ sự phụ thuộc hạ tầng vào API nghiệp vụ.

Giải pháp tốt hơn là DB-first. Có thể dùng hybrid:

```text
Frontend đọc database
Collector cập nhật database định kỳ
Data Engineer có endpoint refresh thủ công khi cần
```

## Thứ tự bạn nên triển khai lại

Trước phần Source API, chen thêm một giai đoạn tích hợp NiFi:

1. Hoàn thiện ORM model.
2. Xác định mapping NiFi process group → source.
3. Viết `NifiClient`.
4. Viết metadata sync.
5. Chạy sync và kiểm tra dữ liệu `nifi_source`, `nifi_component`.
6. Viết metric collector.
7. Kiểm tra dữ liệu xuất hiện trong `metric_history`.
8. Sau đó viết `list_sources()`.
9. Viết `get_source_by_id()`.
10. Viết `get_latest_metric()`.
11. Cuối cùng viết `calculate_availability()`.

File [call_api.py](<./src/web/backend/test/call_api.py>) trước đó đã có một số thử nghiệm gọi NiFi như lấy token, processor và scheduling. Bạn có thể tách phần giao tiếp HTTP dùng chung từ đó sang `NifiClient`; không nên import trực tiếp file test vào backend production.

> Đọc file nifi\_config.py trước khi thực hiện tiếp. Sau đó lập planning giúp tôi phần này đi. Có thứ tự thực hiện từ đầu đến cuối.

<details><summary>1 previous message</summary>

> Mình sẽ đọc `nifi_config.py` trước như bạn yêu cầu, rồi đối chiếu với hai file `nifi_client.py`, `.env`, Docker Compose và phần gọi NiFi thử nghiệm hiện có. Sau đó mình lập roadmap tích hợp NiFi REST API từ cấu hình → client → đồng bộ metadata → collector metric → service/API → test, không sửa code.
</details>

Mình đã đọc `nifi_config.py` và các file liên quan. Trước khi xây dựng cơ chế đồng bộ NiFi, có một số lỗi kiến trúc cần xử lý trước.

## Vấn đề hiện tại

### 1. Import trong `nifi_client.py` đang sai

[clients/nifi_client.py](<./src/web/backend/clients/nifi_client.py>) đang có:

```python
from backend.config.nifi_config import NifiClient
```

Nhưng `nifi_config.py` chỉ khai báo `NifiConfig`, không có `NifiClient`. File client phải import `NifiConfig`, sau đó tự định nghĩa class `NifiClient`.

### 2. `AuthService` có nguy cơ lỗi import

`auth_service.py` trước đó import:

```text
get_secret_key
get_algorithm
get_access_token_expire_minutes
```

Nhưng hiện các hàm này đã nằm trong class `NifiConfig`, không còn là function cấp module. Backend có thể lỗi ngay khi khởi động.

Quan trọng hơn, cấu hình JWT không thuộc NiFi. Nên tách:

```text
config/
├── nifi_config.py
├── auth_config.py
└── database.py
```

`NifiConfig` chỉ quản lý cấu hình NiFi. `AuthConfig` quản lý JWT.

### 3. Tên biến môi trường chưa nhất quán

`.env` đang dùng:

```text
nifi_url
nifi_username
nifi_password
```

nhưng thông báo lỗi lại nói:

```text
NIFI_URL
NIFI_USERNAME
NIFI_PASSWORD
```

Nên thống nhất dùng chữ hoa.

### 4. Thiếu cấu hình cần thiết

Cần bổ sung:

```text
NIFI_VERIFY_SSL
NIFI_CA_BUNDLE
NIFI_REQUEST_TIMEOUT_SECONDS
NIFI_ROOT_PROCESS_GROUP_ID
NIFI_MAX_RETRIES
```

### 5. `localhost` không hoạt động trong container

Nếu backend chạy trực tiếp trên Windows:

```text
NIFI_URL=https://localhost:8443/nifi-api
```

Nếu code chạy trong Airflow container:

```text
NIFI_URL=https://nifi:8443/nifi-api
```

Bên trong container, `localhost` là chính container Airflow, không phải container NiFi.

Tương tự, TimescaleDB trong container phải dùng:

```text
postgres_host=timescaledb
postgres_port=5432
```

không phải `localhost:5433`.

---

# Kế hoạch triển khai từ đầu đến cuối

## Giai đoạn 1 — Sửa và chuẩn hóa cấu hình

### 1.1. Tách `AuthConfig`

Tạo:

```text
backend/config/auth_config.py
```

Chuyển sang đó:

```text
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
```

Sau đó `AuthService` chỉ import `AuthConfig`.

### 1.2. Thu gọn `NifiConfig`

`NifiConfig` chỉ chứa:

```text
base_url
username
password
verify_ssl
ca_bundle
request_timeout
root_process_group_id
max_retries
```

Chọn một trong hai cách:

- Dùng instance properties.
- Hoặc dùng `@staticmethod`.

Không nên khai báo method trong class nhưng không ghi rõ cách sử dụng.

### 1.3. Validate cấu hình lúc khởi động

Các biến bắt buộc:

```text
NIFI_URL
NIFI_USERNAME
NIFI_PASSWORD
```

Nếu thiếu thì báo lỗi rõ ràng. Các giá trị số và boolean cũng cần parse an toàn, tránh:

```text
int(None)
```

### 1.4. Tách cấu hình theo môi trường

Ví dụ:

```text
.env.local
.env.docker
```

Local:

```text
NIFI_URL=https://localhost:8443/nifi-api
```

Docker:

```text
NIFI_URL=https://nifi:8443/nifi-api
```

### Kết quả cần đạt

- Backend khởi động không lỗi import.
- `AuthService` không còn phụ thuộc `NifiConfig`.
- Có thể in ra NiFi URL đã được che thông tin nhạy cảm.
- `.env` không được commit vào Git.

---

## Giai đoạn 2 — Xây dựng `NifiClient`

File:

```text
backend/clients/nifi_client.py
```

`NifiClient` chỉ làm nhiệm vụ HTTP, không query database và không chứa nghiệp vụ RF Engineer.

### 2.1. Tạo HTTP session

Dùng `requests.Session` để tái sử dụng kết nối.

Session cần cấu hình:

```text
base URL
timeout
TLS verification
default headers
```

### 2.2. Implement authentication

Method:

```text
authenticate()
```

Luồng:

```text
POST /access/token
Content-Type: application/x-www-form-urlencoded
        ↓
Nhận access token dạng text
        ↓
Lưu token trong NifiClient
```

Không trả token NiFi cho frontend.

### 2.3. Tạo request wrapper dùng chung

Method nội bộ:

```text
request(method, path, params=None, json=None)
```

Nó chịu trách nhiệm:

- Gắn Bearer token.
- Gắn timeout.
- Kiểm tra status code.
- Parse JSON.
- Nếu gặp `401`, authenticate lại và retry đúng một lần.
- Chuyển lỗi HTTP thành exception riêng.

Nên tạo các exception:

```text
NifiClientError
NifiAuthenticationError
NifiConnectionError
NifiResponseError
```

Không nên raise `FastAPI.HTTPException` bên trong client. Client là infrastructure layer và có thể được Airflow sử dụng ngoài FastAPI.

### 2.4. Các method read-only đầu tiên

Ưu tiên các method đọc:

```text
get_root_process_group()
get_process_group(process_group_id)
get_child_process_groups(process_group_id)
get_processors(process_group_id)
get_connections(process_group_id)
get_process_group_status(process_group_id)
get_processor(processor_id)
```

Đường dẫn chính xác nên được xác minh từ Swagger của chính NiFi 2.0 đang chạy, vì response và endpoint có thể khác giữa các phiên bản:

```text
https://localhost:8443/nifi-api/swagger
```

### Kết quả cần đạt

Chạy script kiểm tra độc lập và lấy được:

- Access token.
- Root process group.
- Danh sách child process group.
- Danh sách processor.
- Process group status.

Chưa ghi database ở bước này.

---

## Giai đoạn 3 — Kiểm thử kết nối NiFi

Trước khi xây dựng sync service, tạo một smoke test độc lập.

Luồng kiểm tra:

```text
Khởi tạo NifiConfig
      ↓
Khởi tạo NifiClient
      ↓
Authenticate
      ↓
Lấy root process group
      ↓
In tên và ID các child group
      ↓
Lấy status của một group
```

Cần test:

| Trường hợp | Kết quả mong đợi |
|---|---|
| Đúng username/password | Thành công |
| Sai password | Authentication error |
| NiFi chưa chạy | Connection error |
| Timeout | Timeout error |
| Token hết hạn | Tự đăng nhập lại một lần |
| JSON không hợp lệ | Response error |
| Certificate tự ký | Hoạt động theo cấu hình local |

Không dùng `verify=False` cố định trong code. Nếu cần cho local, điều khiển bằng biến môi trường.

---

## Giai đoạn 4 — Xác định mapping NiFi → database

Đây là bước nghiệp vụ bắt buộc trước khi đồng bộ.

Bạn cần quyết định một source ENM tương ứng với gì trong NiFi. Khuyến nghị:

```text
Một source ENM = một process group con
```

Ví dụ:

```text
Root Process Group
├── ENM01
├── ENM02
└── ENM06
```

Mapping:

| NiFi | Database |
|---|---|
| Process group UUID | `nifi_process_group.group_id` |
| Process group name | `nifi_process_group.group_name` |
| ENM code | `nifi_source.source_id` |
| Internal PG database ID | `nifi_source.process_group_id` |
| Processor UUID | `nifi_component.component_id` |
| Processor state | `nifi_component.status` |
| Concurrent tasks | `nifi_component.concurrent_tasks` |

Cần quy định cách lấy:

```text
vendor
remote_path
source name
```

Có thể lấy từ:

- NiFi parameter context.
- Processor properties.
- Naming convention.
- File mapping cấu hình.
- Bảng cấu hình do Data Engineer quản lý.

Không nên đoán vendor chỉ dựa trên tên process group.

### Kết quả cần đạt

Viết được một tài liệu mapping mẫu:

```text
NiFi JSON path → database column
```

cho một process group ENM thực tế.

---

## Giai đoạn 5 — Đồng bộ metadata

Tạo:

```text
backend/services/nifi_sync_service.py
```

Service này dùng `NifiClient` và SQLAlchemy session.

Các method:

```text
sync_process_groups()
sync_sources()
sync_components()
sync_all_metadata()
```

### Thứ tự đồng bộ

```text
Process groups
      ↓
Sources
      ↓
Processors/connections
      ↓
Components
```

Phải đồng bộ process group trước vì `nifi_source.process_group_id` là foreign key.

### Dùng upsert

Mỗi lần sync:

```text
NiFi ID đã tồn tại → UPDATE
NiFi ID chưa tồn tại → INSERT
```

Không tạo bản ghi trùng khi chạy lại.

Các khóa dùng để nhận diện:

```text
nifi_process_group.group_id
nifi_source.source_id
nifi_component.component_id
```

### Xử lý đối tượng bị xóa khỏi NiFi

Không nên xóa ngay khỏi database vì có thể phá foreign key và lịch sử.

Nên bổ sung:

```text
is_active
last_seen_at
```

Nếu đối tượng không xuất hiện trong lần sync:

```text
is_active = false
```

### Kết quả cần đạt

Chạy sync nhiều lần nhưng:

- Không có bản ghi trùng.
- Metadata được cập nhật.
- Quan hệ process group, source và component đúng.
- Đối tượng mất khỏi NiFi được đánh dấu inactive.

---

## Giai đoạn 6 — Thu thập metric

Tạo:

```text
backend/services/nifi_metric_service.py
```

và job:

```text
backend/jobs/collect_nifi_metrics.py
```

Hoặc Airflow DAG:

```text
dags/collect_nifi_metrics.py
```

### Luồng collector

```text
Lấy danh sách source active từ database
        ↓
Lấy status từ NiFi
        ↓
Tổng hợp metric theo source
        ↓
INSERT metric_history
```

Không update bản ghi metric cũ. `metric_history` là time-series nên mỗi lần thu thập tạo một snapshot mới.

### Xác minh ý nghĩa rate

Cần kiểm tra response thật của NiFi để biết:

- Rate là tức thời hay tính trên một cửa sổ thời gian.
- Count là giá trị hiện tại hay tích lũy.
- `queued_count` nằm ở process group status hay connection status.
- `concurrent_tasks` cần tổng hay maximum của processor.

Không nên map field chỉ dựa trên tên gần giống.

### Khi collector lỗi

- Rollback transaction.
- Ghi log lỗi.
- Không ghi metric giả bằng `0`.
- Không đổi source thành `UNAVAILABLE`.
- API sau đó nên trả `UNKNOWN` nếu dữ liệu quá cũ.

### Kết quả cần đạt

Sau nhiều lần chạy:

```sql
SELECT *
FROM metric_history
ORDER BY recorded_at DESC;
```

phải thấy chuỗi snapshot theo thời gian cho từng source.

---

## Giai đoạn 7 — Lập lịch collector

Vì project đã có Airflow, bạn có thể dùng Airflow DAG.

DAG gồm hai task:

```text
sync_nifi_metadata
        ↓
collect_nifi_metrics
```

Tần suất:

- Metadata: ít thường xuyên.
- Metric: thường xuyên hơn.

Có thể tách thành hai DAG để có schedule độc lập.

Trong Airflow container cần cấu hình:

```text
NIFI_URL=https://nifi:8443/nifi-api
POSTGRES_HOST=timescaledb
POSTGRES_PORT=5432
PYTHONPATH=/opt/airflow/project/src/web
```

DAG cần:

- Retry có giới hạn.
- Retry delay.
- Execution timeout.
- Không chạy chồng nhiều collector.
- Log số source thành công/thất bại.

---

## Giai đoạn 8 — Xây dựng `SourceService`

Chỉ sau khi database có dữ liệu NiFi thật mới triển khai:

```text
list_sources()
get_source_by_id()
get_latest_metric()
calculate_availability()
```

Vai trò:

```text
NifiClient        → lấy dữ liệu hạ tầng
NifiSyncService   → ghi metadata
MetricCollector   → ghi metric
SourceService     → đọc dữ liệu phục vụ nghiệp vụ
```

`SourceService` không nên gọi NiFi trong request của frontend.

Khi chưa có ngưỡng tải được kiểm chứng:

```text
Source stopped          → UNAVAILABLE
Không có metric         → UNKNOWN
Metric không còn mới    → UNKNOWN
NiFi backpressure       → HIGH_LOAD
Còn lại                 → AVAILABLE
```

Không dùng `BUSY_QUEUE_COUNT` hoặc `HIGH_LOAD_QUEUE_COUNT` tùy ý.

---

## Giai đoạn 9 — Source API

Tạo:

```text
schemas/source_schemas.py
services/source_service.py
controllers/source_controller.py
routes/source_route.py
```

API:

```http
GET /radio/sources
GET /radio/sources/{source_id}
GET /radio/sources/{source_id}/availability
```

API chỉ đọc database và phải kiểm tra role RF Engineer.

Không trả cho RF Engineer:

```text
processor properties
processor revision
concurrent tasks
NiFi access token
raw NiFi response
```

---

## Giai đoạn 10 — Kiểm thử tổng thể

### Unit test

Mock `NifiClient` để test:

- Parse process group.
- Parse processor.
- Parse metric.
- Upsert.
- Availability khi thiếu metric.

### Integration test

Chạy với NiFi local:

```text
NiFi → client → sync service → TimescaleDB
```

Kiểm tra:

- Metadata đúng.
- Foreign key đúng.
- Không trùng dữ liệu.
- Metric được ghi theo thời gian.
- NiFi tắt không làm API backend 500.
- API trả `UNKNOWN` khi collector mất kết nối lâu.

## Thứ tự thực hiện ngắn gọn

```text
1. Tách AuthConfig khỏi NifiConfig
2. Chuẩn hóa biến môi trường
3. Sửa các import đang lỗi
4. Viết NifiClient
5. Test đăng nhập NiFi
6. Test đọc process group/status
7. Chốt mapping NiFi → database
8. Viết metadata sync service
9. Đồng bộ process group
10. Đồng bộ source
11. Đồng bộ component
12. Viết metric collector
13. Lập lịch bằng Airflow
14. Viết SourceService
15. Viết Source API
16. Test toàn bộ luồng
```

Ưu tiên trước mắt là hoàn thành bước 1–6. Chưa nên viết `list_sources()` hoặc `calculate_availability()` hoàn chỉnh cho đến khi bạn đã gọi được NiFi REST API và kiểm tra được JSON thực tế trả về.

> Tôi đã sửa lại rồi. Vậy NIfiConfig đã đúng chưa và còn gì nữa không ?

<details><summary>2 previous messages</summary>

> Mình sẽ kiểm tra `NifiConfig` sau khi bạn sửa, đồng thời đối chiếu cách nó được import/sử dụng trong `AuthService`, `AuthConfig`, `.env` và `NifiClient`. Mình chỉ review và chỉ ra phần còn thiếu hoặc có thể gây lỗi, không sửa code.
>
> Kết quả review: `NifiConfig` đã đúng hơn ở chỗ có `@staticmethod` và chỉ còn cấu hình NiFi, nhưng toàn bộ backend chưa chạy nhất quán vì vẫn còn import cũ trong `AuthService` và file test. Mình kiểm tra nhanh bằng import thực tế để phân biệt lỗi chắc chắn với các cải tiến khuyến nghị.
</details>

`NifiConfig` hiện đã hoạt động cho hai chức năng cơ bản:

- Đọc NiFi URL.
- Đọc username/password.

Mình đã chạy thử và hai method này trả dữ liệu thành công. Tuy nhiên, toàn bộ backend vẫn chưa chạy được vì còn một số điểm cần sửa.

## Lỗi cần sửa ngay

### 1. `AuthService` vẫn import cấu hình JWT từ `nifi_config.py`

Trong [auth_service.py](<./src/web/backend/services/auth_service.py:7>) còn dòng:

```python
from backend.config.nifi_config import (
    get_secret_key,
    get_algorithm,
    get_access_token_expire_minutes,
)
```

Các function này không còn tồn tại nên import thực tế thất bại:

```text
ImportError: cannot import name 'get_secret_key'
```

Bạn đã có:

```python
from backend.config.auth_config import AuthConfig
```

và phía dưới cũng đã gọi `AuthConfig`, vì vậy phải bỏ import cũ từ `nifi_config`.

### 2. File test vẫn dùng cách import cũ

Trong [call_api.py](<./src/web/backend/test/call_api.py:9>) đang import:

```python
from web.backend.config.nifi_config import (
    get_nifi_parameter_token,
    get_nifi_url,
)
```

Cần chuyển sang sử dụng:

```text
NifiConfig.get_nifi_url()
NifiConfig.get_nifi_parameter_token()
```

Đồng thời thống nhất import root là `backend.*`, không trộn `web.backend.*` và `backend.*`.

## Những phần nên hoàn thiện trong `NifiConfig`

### 1. Chuẩn hóa tên biến môi trường

Hiện code đọc biến chữ thường:

```text
nifi_url
nifi_username
nifi_password
```

Nên thống nhất thành:

```text
NIFI_URL
NIFI_USERNAME
NIFI_PASSWORD
```

Sau đó sửa đồng thời `.env`, Docker Compose và code.

### 2. Bổ sung cấu hình HTTP

`NifiClient` sẽ cần thêm:

| Biến | Ý nghĩa |
|---|---|
| `NIFI_VERIFY_SSL` | Có xác minh chứng chỉ HTTPS không |
| `NIFI_CA_BUNDLE` | Đường dẫn CA certificate nếu dùng chứng chỉ riêng |
| `NIFI_REQUEST_TIMEOUT_SECONDS` | Thời gian chờ một request |
| `NIFI_MAX_RETRIES` | Số lần retry lỗi mạng |
| `NIFI_ROOT_PROCESS_GROUP_ID` | Root/group bắt đầu đồng bộ |

Không nhất thiết tất cả đều bắt buộc. Có thể đặt default hợp lý cho timeout và retry.

### 3. Chuẩn hóa URL

Nên loại bỏ dấu `/` cuối URL trước khi sử dụng:

```text
https://localhost:8443/nifi-api/
                                ↑
```

Nếu không, khi nối với `/access/token` có thể tạo:

```text
/nifi-api//access/token
```

### 4. Đổi tên method credentials

`get_nifi_parameter_token()` hơi khó hiểu vì method này chưa trả token, mà chỉ trả username/password để xin token.

Tên rõ hơn:

```text
get_credentials()
get_login_form()
```

Đây là cải tiến readability, không phải lỗi chức năng.

## `AuthConfig` cũng cần chỉnh

[auth_config.py](<./src/web/backend/config/auth_config.py>) chưa có `@staticmethod`.

Hiện gọi bằng:

```python
AuthConfig.get_secret_key()
```

vẫn có thể chạy, nhưng cách khai báo không rõ ràng và sẽ lỗi nếu gọi qua instance:

```python
AuthConfig().get_secret_key()
```

Nên thêm `@staticmethod` cho cả ba method.

Ngoài ra cần validate:

- `SECRET_KEY` không được thiếu/rỗng.
- `ALGORITHM` không được thiếu.
- `ACCESS_TOKEN_EXPIRE_MINUTES` phải là số nguyên dương.

Không nên để `int(None)` phát sinh lỗi khó hiểu.

## `load_dotenv()` nên đặt ở đâu?

Hiện chỉ `nifi_config.py` gọi `load_dotenv()`. Nếu xóa import `NifiConfig` khỏi `AuthService`, việc `AuthConfig` đọc được `.env` sẽ vô tình phụ thuộc vào module khác đã load dotenv trước đó.

Bạn nên chọn một cách nhất quán:

- Gọi `load_dotenv()` một lần ở module settings chung.
- Hoặc mỗi config tự gọi nếu project còn nhỏ.

Không nên để `AuthConfig` phụ thuộc gián tiếp vào `NifiConfig` để `.env` được load.

## `NifiClient` vẫn chưa được triển khai

[clients/nifi_client.py](<./src/web/backend/clients/nifi_client.py>) hiện chỉ có:

```python
from backend.config.nifi_config import NifiConfig
```

Bước tiếp theo là tạo class `NifiClient` với thứ tự:

1. Khởi tạo `requests.Session`.
2. Đọc cấu hình từ `NifiConfig`.
3. Viết `authenticate()`.
4. Viết request wrapper gắn Bearer token.
5. Xử lý timeout, SSL và HTTP errors.
6. Retry đăng nhập một lần khi NiFi trả `401`.
7. Viết `get_root_process_group()`.
8. Viết `get_process_group_status()`.
9. Viết `get_processors()` và `get_connections()`.
10. Chạy smoke test với NiFi local.

## Cần chú ý môi trường chạy

Nếu chạy backend trên Windows:

```text
NIFI_URL=https://localhost:8443/nifi-api
```

Nếu chạy từ Airflow/backend container:

```text
NIFI_URL=https://nifi:8443/nifi-api
```

Không nên dùng chung một `.env` mà không có override theo môi trường.

## Trạng thái hiện tại

| Phần | Trạng thái |
|---|---|
| Đọc URL | Hoạt động |
| Đọc credentials | Hoạt động |
| Tách JWT khỏi NiFi config | Đã làm một phần |
| Import `AuthService` | Đang lỗi |
| Test API cũ | Đang dùng import cũ |
| SSL/timeout/retry config | Chưa có |
| `NifiClient` | Chưa triển khai |
| `.env` được Git ignore | Đã đúng |

Ưu tiên hiện tại: xóa import cũ trong `AuthService`, sửa `AuthConfig`, thống nhất tên biến môi trường, bổ sung cấu hình HTTP, rồi mới bắt đầu viết `NifiClient`.

> Do mỗi lần khởi động lại docker thì nifi sẽ trả lại token khác. Đó là lí do tại sao tôi lại là get\_nifi\_parameter\_token(). Bạn có cải tiến gì khoogn ?

Ý tưởng của bạn đúng: không nên lưu cố định NiFi access token trong `.env`, vì token có thể hết hạn hoặc mất hiệu lực khi NiFi khởi động lại.

Tuy nhiên, tên `get_nifi_parameter_token()` chưa mô tả đúng dữ liệu trả về. Method hiện trả username/password — tức tham số đăng nhập để xin token, không phải token.

## Nên tách trách nhiệm

### Trong `NifiConfig`

Chỉ cung cấp cấu hình và credentials:

```text
get_nifi_url()
get_nifi_credentials()
```

Hoặc đặt tên sát với request hơn:

```text
get_nifi_login_payload()
```

Kết quả:

```python
{
    "username": "...",
    "password": "..."
}
```

### Trong `NifiClient`

Quản lý token động:

```text
authenticate()          → gọi NiFi và nhận token mới
get_access_token()      → lấy token đang cache hoặc đăng nhập
invalidate_token()      → xóa token không còn hợp lệ
request()               → tự gắn token và xử lý 401
```

Phân chia như vậy rõ ràng hơn:

```text
NifiConfig → cung cấp username/password
NifiClient → dùng username/password để lấy và quản lý token
```

## Luồng token khuyến nghị

```text
Khởi tạo NifiClient
        ↓
Chưa có token?
        ↓ Có
POST /access/token
        ↓
Cache token trong RAM
        ↓
Gọi NiFi API
        ↓
Nhận 401?
   ┌────┴────┐
  Không      Có
   ↓          ↓
Trả kết quả  Xóa token cũ
              ↓
         Đăng nhập lại
              ↓
        Retry đúng 1 lần
```

Khi container NiFi restart:

1. `NifiClient` vẫn giữ token cũ.
2. Request tiếp theo có thể nhận `401`.
3. Client xóa token cũ.
4. Gọi lại `/access/token`.
5. Lưu token mới.
6. Thử lại request ban đầu.

## Không lưu token vào database hoặc `.env`

Access token NiFi nên chỉ cache trong RAM:

```python
self._access_token
```

Không nên lưu vào:

```text
.env
PostgreSQL
file JSON
```

Lý do:

- Token chỉ có hiệu lực tạm thời.
- Có thể mất hiệu lực sau khi NiFi restart.
- Là thông tin nhạy cảm.
- Mỗi backend process có thể tự xin token khi cần.

## Skeleton của `NifiClient`

Bạn có thể tự triển khai theo cấu trúc:

```python
class NifiClient:
    def __init__(self):
        self.base_url = ...
        self.credentials = ...
        self._access_token = None
        self.session = requests.Session()

    def authenticate(self) -> str:
        # POST /access/token
        # lưu token vào self._access_token

    def invalidate_token(self) -> None:
        # đặt self._access_token = None

    def request(self, method, path, **kwargs):
        # nếu chưa có token thì authenticate
        # gắn Authorization: Bearer
        # gửi request
        # nếu 401 thì authenticate lại và retry một lần
```

## Chỉ tự đăng nhập lại khi gặp `401`

Không nên authenticate lại với mọi lỗi:

| HTTP status | Xử lý |
|---|---|
| `401` | Token không hợp lệ, đăng nhập lại |
| `403` | Tài khoản không có quyền, không retry |
| `404` | Resource không tồn tại |
| `409` | Xung đột revision/state |
| `500/503` | NiFi lỗi hoặc chưa sẵn sàng |
| Timeout | Retry theo chính sách lỗi mạng |

Nếu retry cả `403`, username/password đúng vẫn không giải quyết được vấn đề quyền.

## Xử lý NiFi chưa khởi động xong

Sau khi Docker báo container started, NiFi có thể vẫn cần thời gian để mở API. `authenticate()` nên có:

- Connection timeout.
- Read timeout.
- Retry hữu hạn.
- Exponential backoff.
- Thông báo lỗi rõ ràng.

Ví dụ chiến lược:

```text
Lần 1 → chờ 1 giây
Lần 2 → chờ 2 giây
Lần 3 → chờ 4 giây
Sau đó báo NiFi unavailable
```

Không retry vô hạn.

## Nếu sử dụng Airflow

Mỗi Airflow task thường là một process riêng, vì vậy token cache trong RAM không được chia sẻ giữa các task. Điều đó không gây vấn đề:

```text
Task bắt đầu
→ tạo NifiClient
→ authenticate
→ gọi API
→ task kết thúc
```

Đối với FastAPI chạy lâu dài, cache token trong instance giúp hạn chế việc đăng nhập lại liên tục.

## Tên method nên dùng

Khuyến nghị rõ nhất:

```text
NifiConfig.get_nifi_login_payload()
NifiClient.authenticate()
NifiClient.get_access_token()
```

Nếu muốn giữ từ “parameter” vì đây là form parameters của NiFi:

```text
get_nifi_token_request_parameters()
```

cũng chính xác hơn `get_nifi_parameter_token()`.

Tóm lại, cách xử lý token động của bạn là đúng. Cải tiến quan trọng là: config chỉ trả thông tin đăng nhập, còn `NifiClient` chịu trách nhiệm xin token, cache token, phát hiện `401` và tự xin lại token mới.

> Viết task hướng dẫn thực hiện code NifiClient

<details><summary>3 previous messages</summary>

> Mình sẽ tạo một tài liệu task có thể giao cho developer thực hiện `NifiClient`, gồm mục tiêu, phạm vi, thứ tự code, contract method, xử lý token/401, lỗi mạng, tiêu chí nghiệm thu và test cases. Mình sẽ đặt cạnh `task 1.md` sau khi kiểm tra cách bạn đang tổ chức thư mục và trạng thái file client/config hiện tại.
>
> Mình đã xác định task này nên là “Task 2” và chỉ tập trung vào lớp HTTP client read-only: cấu hình, đăng nhập động, cache/refresh token, đọc process group/status/processors/connections và kiểm thử. Task sẽ cố ý chưa chứa đồng bộ database, metric collector, API FastAPI hay thao tác start/stop để phạm vi rõ ràng.
>
> <details><summary>Created a file</summary>
>
> - Wrote `./.codex/skills/backend-architecture/task 2.md` (+373 -0)
>
> </details>
</details>

Đã tạo tài liệu [task 2.md](<./.codex/skills/backend-architecture/task 2.md>) hướng dẫn xây dựng `NifiClient`.

Task bao gồm:

- Phạm vi và các phần chưa thực hiện.
- Hoàn thiện `NifiConfig`.
- Exception hierarchy.
- Authentication và cache token.
- Tự đăng nhập lại khi gặp `401`.
- Request wrapper.
- Các API read-only của NiFi.
- Quy tắc retry, TLS và logging an toàn.
- Unit test bằng mock.
- Smoke test với NiFi Docker.
- Thứ tự thực hiện gồm 13 bước.
- Tiêu chí nghiệm thu rõ ràng.
- Đầu ra dành cho metadata sync và metric collector.

Task cũng quy định `NifiClient` không được phụ thuộc FastAPI, database hoặc logic nghiệp vụ; mọi giao tiếp NiFi trong các task tiếp theo phải đi qua client này.
