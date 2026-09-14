# Chức năng của hệ thống

## 1. Đăng nhập
Người dùng có thể tạo tài khoản và đăng nhập vào trong hệ thống.

## 2. Quản lý yêu cầu download của người dùng
* **Mô tả:** Người dùng chọn OSS/RNC/ENM, khoảng thời gian cần download file theo nhu cầu, và có thể tùy chọn bật/tắt các source không mong muốn. Backend sẽ tiếp nhận request, lưu trữ và theo dõi trạng thái của yêu cầu download.
* **Ví dụ minh họa:** 
  * User yêu cầu download file từ `08:00` đến `10:00`. 
  * Hệ thống cần cung cấp giao diện để user kiểm tra xem yêu cầu đó có thành công hay không, số lượng file bị mất trong khung giờ là bao nhiêu, tổng dung lượng tải về đạt bao nhiêu, v.v.

## 3. Monitoring tải hệ thống
Backend thu thập các metric cần thiết từ Apache NiFi bao gồm:
* `queued_count`: Số lượng flowfile trong queue.
* `queue_bytes`: Dung lượng flowfile trong queue.
* `input_file_rate`: Tốc độ file mới đi vào.
* `input_byte_rate`: Dung lượng file mới đi vào theo thời gian.
* `processed_file_rate`: Tốc độ xử lý file.
* `processed_bytes_rate`: Throughput xử lý theo dung lượng.
* `concurrent_tasks`: Số concurrent task hiện tại được cấu hình.

## 4. Load Optimization
Backend tiếp nhận các metric từ module Monitoring kết hợp với các yêu cầu từ người dùng, từ đó tính toán nhu cầu tài nguyên cần thiết cho các source được chọn dựa trên tải hiện tại của hệ thống, và quyết định phân bổ số lượng concurrent task/thread phù hợp cho từng source.

## 5. NiFi Control and Audit
* **NiFi Control:** Backend tích hợp NiFi REST API để đọc trạng thái processor/process group, thực hiện start/stop processor khi cần thiết, thay đổi số lượng `Concurrent Tasks`, và có thể cập nhật property/scheduling khi hệ thống mở rộng trong tương lai.
* **Audit:** Lưu trữ lịch sử thay đổi để truy vết: *Ai đã yêu cầu gì? Hệ thống đã cấp bao nhiêu tài nguyên? Thời điểm thay đổi là lúc nào? Kết quả thực tế ra sao?*