# Yêu cầu giao diện dành cho Kỹ sư vô tuyến

## 1. Mục tiêu giao diện

Giao diện dành cho **Kỹ sư vô tuyến (Radio Engineer)** tập trung vào nhu cầu khai thác dữ liệu Cell Trace theo source, thay vì các thông số vận hành kỹ thuật sâu của hệ thống.

Mục tiêu chính:

- Cho phép người dùng nhanh chóng tạo yêu cầu download dữ liệu theo source.
- Theo dõi trạng thái các yêu cầu đã tạo.
- Xem trạng thái khả dụng của source trước khi gửi yêu cầu.
- Xem lịch sử download để kiểm tra các yêu cầu đã hoàn thành hoặc thất bại.

## 2. Phạm vi chức năng

Giao diện của Kỹ sư vô tuyến gồm các chức năng chính:

1. Dashboard.
2. Tạo yêu cầu download theo source.
3. Xem các yêu cầu download của cá nhân.
4. Xem lịch sử download.

Các chức năng liên quan trực tiếp đến vận hành NiFi như thay đổi `Concurrent Tasks`, start/stop processor, xem allocation history chi tiết hoặc can thiệp optimizer **không thuộc phạm vi giao diện Kỹ sư vô tuyến**.

---

## 3. Menu điều hướng

Menu chính đề xuất:

```text
Dashboard
Create Download Request
My Requests
Download History
```

Các route tương ứng:

```text
/radio/dashboard
/radio/download/new
/radio/requests
/radio/history
```

---

## 4. Dashboard

Dashboard đóng vai trò trang tổng quan sau khi người dùng đăng nhập.

### 4.1. Thông tin cần hiển thị

- Số request đang hoạt động.
- Số request đã hoàn thành gần đây.
- Trạng thái source mà người dùng thường xuyên sử dụng.
- Trạng thái tải tổng quát của hệ thống ở mức dễ hiểu.
- Cảnh báo nếu source đang bận hoặc quá tải.

### 4.2. Hành động chính

Dashboard cần có nút nổi bật:

```text
+ Create Download Request
```

Nút này chuyển người dùng sang trang tạo yêu cầu download mới.

### 4.3. Mức độ hiển thị thông tin kỹ thuật

Không cần hiển thị trực tiếp quá nhiều metric kỹ thuật như:

- `concurrent_tasks`
- `input_file_rate`
- `processed_file_rate`
- `queue_bytes`

Thay vào đó, hệ thống nên tổng hợp thành trạng thái dễ hiểu như:

```text
Available
Busy
High Load
Unavailable
```

---

## 5. Tạo yêu cầu download theo source

Đây là chức năng nghiệp vụ chính của Kỹ sư vô tuyến.

### 5.1. Các trường nhập liệu

Người dùng cần cung cấp:

- Source/ENM cần download.
- Thời gian bắt đầu.
- Thời gian kết thúc.

Ví dụ:

```text
Source: ENM06
From: 14/09/2026 10:00
To:   14/09/2026 12:00
```

### 5.2. Thông tin bổ sung sau khi chọn source

Sau khi người dùng chọn source, giao diện có thể hiển thị:

- Tên source.
- Vendor.
- Trạng thái hiện tại.
- Mức tải hiện tại.
- Source có đang khả dụng để tiếp nhận request hay không.

Ví dụ:

```text
ENM06
Vendor: Ericsson
Status: Available
Current Load: Moderate
```

### 5.3. Kiểm tra khả năng phục vụ

Trước khi tạo request chính thức, hệ thống nên có bước kiểm tra:

```text
Select source + time
        ↓
Check availability
        ↓
User confirms
        ↓
Create request
```

### 5.4. Hành động cuối form

```text
[Cancel]
[Submit Request]
```

---

## 6. My Requests

Trang `My Requests` hiển thị các yêu cầu thuộc người dùng hiện tại.

### 6.1. Các cột đề xuất

| Trường | Ý nghĩa |
|---|---|
| Request ID | Mã yêu cầu |
| Source | Source/ENM được yêu cầu |
| Time Range | Khoảng thời gian download |
| Status | Trạng thái hiện tại |
| Created At | Thời điểm tạo request |
| Action | Xem chi tiết |

Ví dụ:

| ID | Source | Time Range | Status | Action |
|---|---|---|---|---|
| 105 | ENM06 | 10:00-12:00 | RUNNING | View |
| 104 | ENM03 | 08:00-10:00 | COMPLETED | View |
| 103 | ENM02 | 06:00-07:00 | FAILED | View |

### 6.2. Trạng thái request

Các trạng thái có thể gồm:

```text
PENDING
SCHEDULED
RUNNING
COMPLETED
FAILED
REJECTED
```

---

## 7. Download History

Trang lịch sử dùng để xem các request đã kết thúc.

Cần hỗ trợ tối thiểu:

- Xem request đã `COMPLETED`.
- Xem request đã `FAILED`.
- Xem request bị `REJECTED`.
- Lọc theo source.
- Lọc theo khoảng thời gian.
- Xem chi tiết một request.

Nếu request thất bại, giao diện cần hiển thị lý do thất bại ở mức phù hợp với người dùng.

---

## 8. Chi tiết request

Khi người dùng chọn `View`, trang chi tiết cần hiển thị:

- Request ID.
- Source.
- Thời gian yêu cầu.
- Thời điểm tạo.
- Thời điểm bắt đầu thực tế.
- Thời điểm hoàn thành.
- Trạng thái hiện tại.
- Lý do thất bại nếu có.

Không cần hiển thị các quyết định phân bổ tài nguyên nội bộ như số thread được cấp cho source nếu người dùng không có quyền Orchestrator.

---

## 9. Nguyên tắc UX/UI

Giao diện dành cho Kỹ sư vô tuyến cần ưu tiên:

- Thao tác nhanh.
- Ít thuật ngữ hạ tầng.
- Trạng thái dễ hiểu.
- Không bắt người dùng hiểu NiFi hoặc thuật toán phân bổ tải.
- Luôn cho biết request đang ở bước nào.
- Cảnh báo rõ khi source đang không khả dụng.

---

## 10. Phân quyền

Kỹ sư vô tuyến chỉ được truy cập các chức năng phục vụ khai thác dữ liệu.

Không được phép:

- Thay đổi `Concurrent Tasks`.
- Start/Stop NiFi Processor.
- Chỉnh cấu hình NiFi.
- Xem hoặc chỉnh allocation của toàn hệ thống.
- Quản lý tài khoản người dùng.

Các API tương ứng cũng phải kiểm tra quyền ở backend, không chỉ ẩn chức năng trên frontend.

---

## 11. Layout tổng quát đề xuất

```text
┌──────────────────────────────────────────────────────────────┐
│ Dashboard                                      User          │
├──────────────────────────────────────────────────────────────┤
│ + Create Download Request                                    │
├─────────────────────────────────┴────────────────────────────┤
│ System Status                                                │
│ 6 / 10 sources active   Queue: 32k files   Load: Moderate    │
└──────────────────────────────────────────────────────────────┘
│ My Active Requests                                           │
│ #105 ENM06   10:00 → 12:00   SCHEDULED                     │
│ #104 ENM03   08:00 → 10:00   RUNNING                       │
├───────────────────────────────┬──────────────────────────────┤
│ Source Availability                                          │
│ ENM01   Available                                            │
│ ENM02   Busy                                                 │
│ ENM03   Available                                            │
├──────────────────────────────────────────────────────────────┤
│ Recent Download History                                      │
├──────────────────────────────────────────────────────────────┤
│ Download Request History                                     │
│ #105 ENM06   10:00 → 12:00   SCHEDULED                     │
│ #104 ENM03   08:00 → 10:00   DOWNLOADING  65%              │
│ #103 ENM02   06:00 → 07:00   COMPLETED                     │
├─────────────────────────────────┬────────────────────────────┤
```

---

## 12. Ưu tiên triển khai

Thứ tự triển khai được tổ chức theo quan hệ phụ thuộc giữa dữ liệu, API và giao diện. Không bắt đầu từ Dashboard vì Dashboard cần tổng hợp dữ liệu từ source và download request đã hoạt động ổn định.

### Giai đoạn 1: Hoàn thiện nền tảng dữ liệu

1. Hoàn thiện SQLAlchemy model cho `nifi_source`, `download_request` và `metric_history`.
2. Khai báo relationship giữa user, source và download request.
3. Chuẩn hóa enum trạng thái request: `PENDING`, `SCHEDULED`, `RUNNING`, `COMPLETED`, `FAILED`, `REJECTED`.
4. Tạo migration, foreign key, index và constraint cần thiết.
5. Chuẩn hóa timezone cho toàn bộ trường thời gian.

Kết quả cần đạt: backend đọc và ghi được dữ liệu mẫu bằng ORM, các constraint hoạt động đúng.

### Giai đoạn 2: Hoàn thiện xác thực và phân quyền

1. Hoàn thiện `GET /auth/me`.
2. Kiểm tra access token và lấy user hiện tại từ database.
3. Áp dụng role `Radio Frequency Engineer` cho toàn bộ API `/radio/*`.
4. Chặn Radio Frequency Engineer truy cập API điều khiển hoặc cấu hình NiFi.

Kết quả cần đạt: không có token trả `401`, sai role trả `403`, đúng role được phép truy cập.

### Giai đoạn 3: Danh mục và trạng thái source

1. Xây dựng `GET /radio/sources`.
2. Xây dựng `GET /radio/sources/{source_id}`.
3. Đọc metric mới nhất và tổng hợp thành trạng thái dễ hiểu: `Available`, `Busy`, `High Load`, `Unavailable`.
4. Kiểm tra source còn tồn tại và có thể tiếp nhận request.

Kết quả cần đạt: form tạo request có thể tải danh sách source và hiển thị trạng thái hiện tại.

### Giai đoạn 4: Create Download Request

1. Xây dựng schema request/response.
2. Xây dựng `POST /radio/download-requests`.
3. Validate source, khoảng thời gian và khả năng tiếp nhận request.
4. Lấy `user_id` từ access token, không nhận `user_id` từ frontend.
5. Tạo request ban đầu với trạng thái `PENDING`.

Kết quả cần đạt: Radio Frequency Engineer tạo được một request hợp lệ và không thể tạo request thay người khác.

### Giai đoạn 5: My Requests và Request Detail

1. Xây dựng `GET /radio/download-requests` có phân trang và lọc theo trạng thái/source.
2. Xây dựng `GET /radio/download-requests/{request_id}`.
3. Mọi truy vấn phải giới hạn theo `current_user.id`.
4. Chỉ trả thông tin nghiệp vụ; không trả cấu hình NiFi hoặc allocation nội bộ.

Kết quả cần đạt: người dùng chỉ xem được request thuộc tài khoản của mình.

### Giai đoạn 6: Xử lý vòng đời request

1. Xây dựng worker hoặc Airflow DAG đọc request `PENDING`.
2. Cập nhật tuần tự `SCHEDULED` → `RUNNING` → `COMPLETED` hoặc `FAILED`.
3. Ghi `started_at`, `completed_at` và `failure_reason`.
4. Đảm bảo việc chạy lại worker không xử lý trùng request.

Kết quả cần đạt: request thay đổi trạng thái theo quá trình download thực tế, không chỉ tồn tại dưới dạng bản ghi tĩnh.

### Giai đoạn 7: Download History

1. Xây dựng `GET /radio/download-requests/history`.
2. Chỉ lấy các trạng thái kết thúc: `COMPLETED`, `FAILED`, `REJECTED`.
3. Hỗ trợ lọc theo source, trạng thái và khoảng ngày.
4. Phân trang và giới hạn dữ liệu theo user hiện tại.

Kết quả cần đạt: màn hình lịch sử hoạt động trên dữ liệu request thật.

### Giai đoạn 8: Dashboard

1. Xây dựng `GET /radio/dashboard` sau khi các API bên trên ổn định.
2. Tổng hợp số request đang hoạt động và đã hoàn thành gần đây.
3. Trả danh sách active request, source thường dùng, source availability và recent history.
4. Không trả các metric kỹ thuật chi tiết không cần thiết cho Radio Frequency Engineer.

Kết quả cần đạt: Dashboard dùng một API tổng hợp và không phải gọi lặp nhiều endpoint để tự tính số liệu.

### Giai đoạn 9: Kiểm thử và tích hợp giao diện

1. Unit test validation và chuyển trạng thái request.
2. Integration test API với PostgreSQL/TimescaleDB.
3. Kiểm thử `401`, `403` và việc cô lập dữ liệu giữa hai user.
4. Kiểm thử phân trang, bộ lọc, timezone và trường hợp metric quá cũ.
5. Kết nối lần lượt các trang: Create Request → My Requests → Request Detail → History → Dashboard.

Kết quả cần đạt: hoàn thành luồng end-to-end từ đăng nhập, tạo request đến khi xem kết quả trong lịch sử.
