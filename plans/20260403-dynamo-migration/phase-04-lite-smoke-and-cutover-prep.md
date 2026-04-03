# Phase 04 Lite - Smoke Test và chuẩn bị cutover Dynamo-only

## 1. Mục tiêu

- Không backfill.
- Không dual-write.
- Không parity với Mongo.
- Chỉ xác nhận rằng refactor phase 3 đã đủ ổn để hệ thống chạy bằng DynamoDB.
- File này chỉ áp dụng sau khi đã có Dynamo thật để chạy.
- Nếu hiện tại chưa init Dynamo, **không làm file này**, chỉ làm `Phase 03A code-only`.

## 2. Điều kiện để được bắt đầu

- `Phase 03A` đã xong.
- `Phase 03B` có thể bắt đầu vì đã có Dynamo để boot/test.
- Không còn blocker runtime ở auth/class/exam/conversation/OTP/violation.

## 3. Scope cụ thể

### 3.1 Infra tối thiểu

- Có file Terraform hoặc cấu hình table Dynamo cho:
- `users`
- `classes`
- `class_teacher_assignments`
- `exams`
- `submissions`
- `violations`
- `conversations`
- `otps`

- GSI đúng với phase 02 schema.
- TTL bật cho `otps.expire_at_epoch` nếu hạ tầng hỗ trợ.

### 3.2 App config tối thiểu

- `app_config.py` có đủ `DYNAMODB_*` để boot local/dev/test.
- `.env.example` có biến Dynamo cần thiết.
- App không cần `MONGO_*` để chạy phase này.

### 3.3 Seed dữ liệu tối thiểu nếu cần

- 1 admin
- 1 teacher
- 1 student
- 1 class
- 1 exam

Seed chỉ nhằm phục vụ smoke test. Không cần script backfill.

## 4. System check chi tiết

### 4.1 Boot checks

- App startup không crash.
- Lifespan hoàn tất.
- `app.state.persistence` được khởi tạo.
- `app.state.conversation_handler` được khởi tạo.
- Health endpoint trả về bình thường.

### 4.2 Auth checks

- login thành công với user seed
- token decode và `/user-info` đúng
- forgot password sinh OTP
- reset password đổi được mật khẩu

### 4.3 Class checks

- admin tạo class mới được
- list class theo role hoạt động
- get class detail đúng
- add/remove student cập nhật đúng state liên quan

### 4.4 Exam checks

- teacher tạo exam được
- list exam theo teacher được
- student thấy exam đúng class
- verify secret key đúng
- submit exam không bị double submit
- exam status phản ánh đúng sau submit
- results summary đọc được counters

### 4.5 Conversation checks

- tạo conversation được
- ghi message đầu tiên được
- title được update đúng behavior cũ nếu rule đó còn giữ
- list/latest/get/delete đều chạy
- cache không làm sai dữ liệu

### 4.6 Violation checks

- log violation không crash
- query violation theo class hoặc exam chạy được
- camera flow không lỗi import nếu route camera bật

## 5. Lệnh/kiểu kiểm tra Claude Code phải chạy

### 5.1 Kiểm tra import/runtime surface

- grep toàn backend để tìm:
- `MongoClient`
- `motor`
- `pymongo`
- `src.database`
- `get_violation_logger`

Mục đích:

- xác định cái nào còn nằm trên runtime path
- chưa cần xóa sạch ở phase này, nhưng phải chắc chắn runtime chính không phụ thuộc

### 5.2 Kiểm tra boot

- chạy app local với config Dynamo
- gọi health endpoint
- nếu app không boot được, phase 03 chưa xong

### 5.3 Kiểm tra smoke API

- gọi các route chính bằng test client hoặc integration test
- ưu tiên auth, class, exam, conversation

### 5.4 Kiểm tra repository level

- CRUD user
- CRUD class
- create/list exam
- create/list/delete conversation
- save/get/delete OTP
- upsert/list violation

## 6. Điều gì không thuộc phase này

- Không tối ưu scan thành query nếu chưa phải blocker correctness.
- Không xóa sạch toàn bộ Mongo legacy code.
- Không dọn hết test cũ Mongo nếu chúng chưa chạm runtime path mới.
- Không đổi API contract.
- Không dùng phase này để sửa tiếp các vấn đề linter/formatting tồn từ phase 03A.

## 7. Kết quả đầu ra bắt buộc

Claude Code phải ghi một report nêu rõ:

- app có boot bằng Dynamo-only path hay không
- smoke test nào pass
- smoke test nào fail
- còn dependency Mongo nào nằm trên runtime path
- có thể qua phase 5 hay chưa

## 8. Điều kiện để qua phase 5

- App boot ổn với Dynamo path
- Smoke test core flows pass
- Không còn blocker correctness lớn
- Mongo chỉ còn là legacy cleanup, không còn là dependency bắt buộc để app chạy

## 9. Unresolved questions

- Có cần seed script chính thức cho local/dev hay dùng fixture/test helper là đủ?
- Camera routes có bắt buộc nằm trong smoke test core hay được coi là optional feature?
