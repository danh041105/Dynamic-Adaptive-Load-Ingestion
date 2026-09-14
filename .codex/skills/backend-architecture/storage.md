# Giải pháp về mặt lưu trữ

Hệ thống sử dụng cơ sở dữ liệu quan hệ kết hợp với TimescaleDB, bao gồm tổng cộng 7 bảng chính:

## 1. Thiết kế cơ sở dữ liệu

### 1.1. Bảng `users`
* **Chức năng:** Lưu trữ thông tin tài khoản người dùng và phân quyền truy cập.

### 1.2. Bảng `nifi_process_group`
* **Chức năng:** Lưu trữ cấu trúc Process Group bên phía NiFi, giúp backend xác định Process Group nào tương ứng với khu vực hoặc luồng xử lý nào.

### 1.3. Bảng `nifi_source`
* **Chức năng:** Lưu trữ thông tin cơ bản của một processor/source, giúp kiểm soát source đó thuộc Process Group nào, đường dẫn SFTP ở đâu và thuộc vendor nào.

### 1.4. Bảng `nifi_component`
* **Chức năng:** Bảng gom chung các thành phần *Processor*, *Funnel* và *Connection*, giúp backend nắm bắt được cấu trúc chi tiết (Ví dụ: `ENM03` hiện đang có những component NiFi nào).

* **Ví dụ Processor:**
  ```json
  {
    "id": 101,
    "source_id": 3,
    "component_id": "fetch-sftp-uuid",
    "component_name": "FetchSFTP ENM03",
    "component_type": "PROCESSOR",
    "processor_type": "FetchSFTP",
    "concurrent_tasks": 3,
    "status": "RUNNING"
  }

* **Ví dụ Connection:**
  ```json
    {
    "id": 102,
    "source_id": 3,
    "component_id": "connection-uuid",
    "component_name": "Queue ListSFTP -> FetchSFTP",
    "component_type": "CONNECTION",
    "source_component_id": "list-sftp-uuid",
    "destination_component_id": "fetch-sftp-uuid",
    "status": "ACTIVE"
    }

**1.5. Bảng download_request**;

* **Chức năng:** Đây là bảng lưu yêu cầu nghiệp vụ từ người dùng.

* **Ví dụ: Người dùng yêu cầu bật download file từ 10h đến 11h sáng**
  ```json
    {
    "id": 500,
    "user_id": 1,
    "source_id": 3,
    "start_time": "2026-09-13 10:00",
    "end_time": "2026-09-13 11:00",
    "status": "RUNNING",
    "created_at": "09:55",
    "started_at": "10:00",
    "completed_at": null
    }


**1.6. Bảng metric_history (Lưu bằng timescaleDB)**

* **Chức năng:** Định kỳ 1 phút, Mỗi source sẽ lưu snapshot xuống database. Bảng này sẽ là đầu vào cho **Chức năng Load Optimization**
* Ví dụ chuỗi thời gian của ENM03:
* 10:05: source_id = 3, recorded_at = 10:05, queued_count = 8200, queue_bytes = 71 GB, input_file_rate = 500 file/min, input_byte_rate = 6.2 GB/min, processed_file_rate = 350 file/min, processed_byte_rate = 4.4 GB/min, concurrent_tasks = 3  

* 10:06: queue = 8350, input = 510, processed = 355, tasks = 3  

* 10:07: queue = 8500, input = 505, processed = 360, tasks = 3  

* Phân tích từ Optimizer: Dựa vào chuỗi metric trên, khi thấy chỉ số input > processed, hệ thống nhận diện tình trạng backlog (hàng đợi) đang tăng dần.

**1.7. Bảng allocation_history (Lưu bằng timescaleDB)**

* **Chức năng:** Ghi lại toàn bộ lịch sử các quyết định và hành động điều chỉnh tài nguyên của module Optimizer.
* Ví dụ bản ghi tại 10:08: Khi Optimizer quyết định nâng tài nguyên của ENM03 từ 3 tasks lên 5 tasks

 ```json
    {
    "id": 900,
    "source_id": 3,
    "request_id": 500,
    "old_concurrent_tasks": 3,
    "new_concurrent_tasks": 5,
    "reason": "USER_REQUEST_AND_BACKLOG_INCREASING",
    "queued_count": 8500,
    "queue_bytes": "73 GB",
    "input_file_rate": 505,
    "processed_file_rate": 360,
    "created_at": "10:08"
    }
* Ý nghĩa thực tiễn
* Truy vết nguyên nhân: Nhờ liên kết với request_id = 500, hệ thống biết chính xác việc tăng task này gắn liền với yêu cầu nghiệp vụ nào của người dùng.
* Đánh giá hiệu quả: Sau khi điều chỉnh, các bản ghi tiếp theo trong metric_history cho thấy tốc độ xử lý đã cải thiện rõ rệt (10:09 --> processed = 430, 10:10 --> processed = 480, 10:11 --> processed = 510), lượng queue bắt đầu giảm --> chứng minh quyết định tối ưu mang lại hiệu quả thực tế.
