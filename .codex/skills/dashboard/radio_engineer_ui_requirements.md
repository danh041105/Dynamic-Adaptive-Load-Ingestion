# Yêu cầu giao diện dành cho Kỹ sư vô tuyến

## 1. Mục tiêu giao diện

Giao diện dành cho **Kỹ sư vô tuyến (Radio Engineer)** tập trung vào nhu cầu khai thác dữ liệu Cell Trace theo source, thay vì các thông số vận hành kỹ thuật sâu của hệ thống.

Mục tiêu chính:

- Cho phép người dùng nhanh chóng tạo yêu cầu download dữ liệu theo source.
- Theo dõi trạng thái các yêu cầu đã tạo.
- Xem trạng thái khả dụng của source trước khi gửi yêu cầu.
- Nhận gợi ý từ hệ thống nếu thời gian yêu cầu chưa phù hợp với tải hiện tại.
- Xem lịch sử download để kiểm tra các yêu cầu đã hoàn thành hoặc thất bại.

---
┌──────────────────────────────────────────────────────────────┐
│ Dashboard                                      Nguyễn Văn A  │
├──────────────────────────────────────────────────────────────┤
│                    QUICK DOWNLOAD REQUEST                    │
│ Source/ENM     From                 To                       │
│ [ ENM06 ▼ ]    [ 10:00 14/09 ]      [ 12:00 14/09 ]         │
│                                             [ Download ]     │
├──────────────────────────────────────────────────────────────┤
│ My Active Requests                                           │
│ #105 ENM06   10:00 → 12:00   SCHEDULED                      │
│ #104 ENM03   08:00 → 10:00   DOWNLOADING  65%               │
│ #103 ENM02   06:00 → 07:00   COMPLETED                      │
├─────────────────────────────────┬────────────────────────────┤
│ Source Availability             │ System Recommendation      │
│ ENM01   Available               │ ENM06 can start at 10:00   │
│ ENM02   Busy                    │ Expected completion 12:05  │
│ ENM03   Downloading             │ System load: Normal        │
│ ENM06   Available               │                            │
├─────────────────────────────────┴────────────────────────────┤
│ System Status                                               │
│ 6 / 10 sources active   Queue: 32k files   Load: Moderate   │
└──────────────────────────────────────────────────────────────┘


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
- Gợi ý hoặc cảnh báo nếu source đang bận hoặc quá tải.

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
Show recommendation
        ↓
User confirms
        ↓
Create request
```

### 5.4. Recommendation

Nếu hệ thống đánh giá khoảng thời gian user chọn chưa phù hợp, giao diện cần đưa ra gợi ý.

Ví dụ:

```text
Requested:
ENM06
10:00 → 12:00

System assessment:
Current source load: High

Recommended:
10:30 → 12:30
```

Người dùng có thể chọn:

```text
[Keep original time]
[Use recommended time]
```

### 5.5. Hành động cuối form

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
- Recommendation hoặc thay đổi lịch nếu hệ thống từng đề xuất.

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
- Recommendation phải mang tính hỗ trợ, không làm mất quyền lựa chọn của người dùng nếu nghiệp vụ vẫn cho phép gửi request gốc.

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
│ + Create Download Request                                   │
├──────────────────────────────────────────────────────────────┤
│ My Active Requests                                          │
│ #105 ENM06   10:00 → 12:00   SCHEDULED                     │
│ #104 ENM03   08:00 → 10:00   RUNNING                       │
├───────────────────────────────┬──────────────────────────────┤
│ Source Availability           │ System Recommendation        │
│ ENM01   Available             │ ENM06 currently busy         │
│ ENM02   Busy                  │ Recommended: 10:30 → 12:30  │
│ ENM03   Available             │                              │
├───────────────────────────────┴──────────────────────────────┤
│ Recent Download History                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. Ưu tiên triển khai

Phiên bản đầu tiên nên ưu tiên theo thứ tự:

1. Dashboard cơ bản.
2. Create Download Request.
3. My Requests.
4. Request Detail.
5. Download History.
6. Recommendation dựa trên tải hệ thống.

