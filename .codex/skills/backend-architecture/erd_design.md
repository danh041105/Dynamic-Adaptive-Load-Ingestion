# Thiết kế ERD Database

## 1. Phạm vi

Tài liệu này chỉ tập trung vào thiết kế ERD cho backend của hệ thống.

Database gồm 7 bảng chính:

1. `users`
2. `nifi_process_group`
3. `nifi_source`
4. `nifi_component`
5. `download_request`
6. `allocation_history`
7. `metric_history`

Trong đó:

- `users`, `nifi_process_group`, `nifi_source`, `nifi_component`, `download_request`, `allocation_history` lưu dữ liệu nghiệp vụ.
- `metric_history` lưu dữ liệu metric theo thời gian.

---

## 2. ERD

```text
notation crows-foot

users [icon: user, color: red] {
  user_id int pk
  username string @unique [required]
  hashed_password string [required]
  role string [required]
  created_at datetime
  updated_at datetime
}

nifi_process_group [icon: nifi, color: blue] {
  id int pk
  group_id string @unique [required]
  group_name string [required]
  parent_id int
  level int
  created_at datetime
  updated_at datetime
}

nifi_source [icon: folder, color: green] {
  id int pk
  source_id string @unique [required]
  source_name string [required]
  process_group_id int [required]
  vendor string
  remote_path string
  status string
  schedule_start datetime
  schedule_end datetime
  created_at datetime
  updated_at datetime
}

nifi_component [icon: component, color: orange] {
  id int pk
  source_id int [required]
  component_id string @unique [required]
  component_name string
  component_type string [required]
  processor_type string
  source_component_id string
  destination_component_id string
  concurrent_tasks int
  status string
  created_at datetime
  updated_at datetime
}

download_request [icon: download, color: purple] {
  id int pk
  user_id int [required]
  source_id int [required]
  start_time datetime [required]
  end_time datetime [required]
  status string [required]
  failure_reason string
  created_at datetime
  started_at datetime
  completed_at datetime
}

metric_history [icon: chart, color: cyan] {
  source_id int pk [required]
  recorded_at datetime pk [required]
  queued_count bigint
  queue_bytes bigint
  input_file_rate double
  input_byte_rate double
  processed_file_rate double
  processed_byte_rate double
  concurrent_tasks int
}

allocation_history [icon: activity, color: yellow] {
  id int pk
  source_id int [required]
  request_id int
  old_concurrent_tasks int [required]
  new_concurrent_tasks int [required]
  reason string
  queued_count bigint
  queue_bytes bigint
  input_file_rate double
  input_byte_rate double
  processed_file_rate double
  processed_byte_rate double
  created_at datetime [required] pk
}


nifi_process_group.id - nifi_source.process_group_id
nifi_process_group.id < nifi_process_group.parent_id
nifi_source.id < nifi_component.source_id
users.user_id < download_request.user_id
nifi_source.id < download_request.source_id
nifi_source.id < metric_history.source_id
nifi_source.id < allocation_history.source_id
download_request.id < allocation_history.request_id
```
# Lưu ý
## 3. Thiết kế TimescaleDB

Hai bảng được sử dụng dưới dạng TimescaleDB hypertable:

- `metric_history`
- `allocation_history`

Hai bảng có đặc điểm phát sinh dữ liệu khác nhau nên không sử dụng cùng một `chunk interval`.
- bảng metric_history
---

### 3.1 `metric_history`
`metric_history` lưu snapshot metric theo thời gian của từng ENM.
Ví dụ hệ thống thu thập metric:
```text
1 snapshot / ENM / phút
Với metric_history, giả sử hiện tại có 10 ENM:
10 ENM × 60 phút × 24 giờ
= 14,400 rows/day
- Đặt chunk interval là 1 ngày

### 3.2 `allocation_history`
`allocation_history` sẽ lưu những thay đổi khi có có sự thay đổi về phân bổ tài nguyên
- Đặt chunk interval là 7 ngày



Các quan hệ chính:

- một `nifi_process_group` có nhiều `nifi_source`;
- một `nifi_process_group` có thể có Process Group con;
- một `nifi_source` có nhiều `nifi_component`;
- một `user` có thể tạo nhiều `download_request`;
- một `nifi_source` có thể có nhiều `download_request`;
- một `nifi_source` có nhiều record `metric_history`;
- một `nifi_source` có nhiều record `allocation_history`;
- một `download_request` có thể liên quan đến nhiều lần thay đổi allocation.