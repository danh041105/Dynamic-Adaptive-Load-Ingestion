# Cấu trúc thư mục backend

Khi làm việc bên trong thư mục `backend/`, luôn tuân theo kiến trúc sau:

- `config/`: cấu hình, cơ sở dữ liệu, thiết lập môi trường.
- `models/`: chỉ chứa các mô hình cơ sở dữ liệu/ORM.
- `schemas/`: các lược đồ xác thực yêu cầu/phản hồi (request/response validation).
- `services/`: logic nghiệp vụ và các thao tác cơ sở dữ liệu.
- `controllers/`: điều phối việc xử lý yêu cầu và gọi các services.
- `routes/`: định nghĩa các API routes và kết nối chúng với controllers.
- `dependencies`: kiểm tra quyền và xác thực.
Rules:
- Không đặt logic nghiệp vụ vào routes.
- Không truy cập cơ sở dữ liệu trực tiếp từ routes.
- Tái sử dụng các services, schemas và models hiện có trước khi tạo mới.
- Giữ cho mỗi tính năng được tách biệt và tuân theo phong cách đặt tên có sẵn của dự án.
-Tuyệt đối không chỉnh sửa thư mục __pycache__.