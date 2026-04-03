# Phase 01 - Chuẩn hóa persistence layer

## 1. Mục tiêu
- Cắt hoàn toàn direct dependency từ route/service sang Mongo collection global.
- Tạo một persistence facade/repository layer duy nhất để các phase sau có thể thay backend store mà không phải sửa route/business logic thêm lần nữa.
- Giữ behavior hiện tại càng nguyên vẹn càng tốt trong phase này.

## 2. Files bắt buộc phải rà soát
- `backend/src/main.py`
- `backend/src/auth/dependencies.py`
- `backend/src/auth/otp_storage.py`
- `backend/src/detection/violation_logger.py`
- `backend/src/routers/auth/login.py`
- `backend/src/routers/auth/register.py`
- `backend/src/routers/auth/password.py`
- `backend/src/routers/class_routes.py`
- `backend/src/routers/exam_routes.py`
- `backend/src/conversation/conversation_handler.py`
- `backend/src/database.py`
- `backend/src/database/__init__.py`
- `backend/src/database/class_handler.py`
- `backend/src/database/exam_handler.py`
- `backend/src/database/mongo_client.py`

## 3. Kết quả kiến trúc mong muốn sau phase
- Có một facade duy nhất, ví dụ:
  - `PersistenceFacade`
  - hoặc `AppPersistence`
- Facade expose các repository theo domain:
  - `users`
  - `classes`
  - `class_teacher_assignments`
  - `exams`
  - `submissions`
  - `violations`
  - `conversations`
  - `otps`
- `main.py` inject facade vào `app.state`.
- Các dependency và routes lấy repository qua app state hoặc dependency injection.

## 4. Việc phải làm

### 4.1 Tạo abstraction layer
- Tạo thư mục mới cho persistence, ví dụ:
  - `backend/src/persistence/`
- Định nghĩa interface hoặc protocol cho từng domain repository.
- Tạo facade gom toàn bộ repository vào một object.
- Phase này có thể cho phép implementation tạm thời vẫn dùng Mongo phía dưới, miễn là route không còn biết Mongo tồn tại.

### 4.2 Dọn `main.py`
- `main.py` không còn tự khởi tạo `ClassHandler`, `ExamHandler`, `ConversationHandler` bằng `MongoClient` trực tiếp.
- `main.py` chỉ khởi tạo:
  - persistence facade
  - Redis client
  - SentenceTransformer
- App state chứa facade hoặc domain services được dựng từ facade.

### 4.3 Dọn auth dependency
- `auth.dependencies.py` không import `users_collection`.
- `get_current_user()` phải lấy user qua repository hoặc facade.

### 4.4 Dọn route auth
- `login.py`, `register.py`, `password.py` không import `src.database`.
- Toàn bộ call `find_one`, `insert_one`, `update_one`, `update_many`, `delete_one`, `find` phải đổi thành repository methods có tên rõ nghĩa.

### 4.5 Dọn route class và exam
- `class_routes.py` và `exam_routes.py` không được import `ObjectId`.
- Không được validate ID bằng Mongo-specific logic.
- Validation tối thiểu trong phase này:
  - ID là string không rỗng
  - repository quyết định record có tồn tại hay không

### 4.6 Dọn OTP storage và violation logger
- `otp_storage.py` và `violation_logger.py` không còn import `src.database`.
- OTP và violation phải dùng repository.

### 4.7 Dọn conversation handler
- `conversation_handler.py` không phụ thuộc `MongoClient` nữa.
- Tách logic conversation business với logic persistence.
- Handler chỉ dùng conversation repository + cache + embedding model.

## 5. Interface tối thiểu cần có

### User repository
- `get_by_email(email)`
- `get_by_id(user_id)`
- `create_user(user_doc)`
- `update_user(user_id, fields)`
- `delete_user(user_id)`
- `list_users_by_role(role)`
- `find_users_by_ids(user_ids)`
- `list_students_by_class(class_id)` hoặc equivalent

### Class repository
- `get_by_id(class_id)`
- `get_by_name_grade(name, grade)`
- `create_class(class_doc)`
- `update_class(class_id, fields)`
- `delete_class(class_id)`
- `list_all_classes()`
- `list_classes_for_teacher(teacher_id)`
- `list_classes_for_student(class_name, grade)` hoặc equivalent

### Exam repository
- `get_by_id(exam_id)`
- `create_exam(exam_doc)`
- `update_exam(exam_id, fields)`
- `delete_exam(exam_id)`
- `list_by_teacher(teacher_id)`
- `list_by_class(class_id)`
- `list_all_exams()`

### Submission repository
- `get_by_exam_student(exam_id, student_id)`
- `create_submission(submission_doc)`
- `list_by_exam(exam_id)`
- `list_by_student(student_id)`
- `delete_by_exam_student(exam_id, student_id)`

### Violation repository
- `upsert_violation(exam_id, student_id, payload)`
- `list_by_class(class_id)`
- `list_by_exam(exam_id)`
- `delete_by_exam_student(exam_id, student_id)`

### Conversation repository
- `create_conversation(conversation_doc)`
- `get_conversation(conversation_id, user_id=None)`
- `list_conversations(user_id, limit)`
- `get_latest_conversation(user_id)`
- `append_message(...)`
- `delete_conversation(conversation_id, user_id)`

### OTP repository
- `save_otp(email, purpose, otp, expire_at)`
- `get_otp(email, purpose, otp)`
- `delete_otp(email, purpose)`
- `delete_expired_otps(now)`

## 6. Nguyên tắc code
- Không dùng generic wrapper quá mơ hồ kiểu `run_query`.
- Ưu tiên method name rõ nghĩa theo domain.
- Không cố generic hóa toàn bộ Mongo API sang interface giả.
- Nếu method hiện tại phụ thuộc behavior Mongo quá sâu, tách business logic khỏi storage operation.

## 7. Deliverable của phase
- App compile được.
- Route và service không còn import `src.database`, `MongoClient`, `motor`, `pymongo`, `ObjectId`.
- Chưa cần Dynamo chạy thật trong phase này, nhưng interface phải đủ để phase 2 và 3 gắn implementation mới.

## 8. Acceptance criteria
- `rg -n "from src.database|MongoClient|motor|pymongo|ObjectId" backend/src`
  - chỉ được phép còn xuất hiện ở implementation Mongo tạm thời trong persistence layer
  - không còn xuất hiện ở router, auth dependency, conversation handler, violation logger
- `main.py` dùng facade thay vì dựng Mongo handlers trực tiếp.
- Unit tests có thể patch repository/facade thay vì patch collection global.

## 9. Report phải ghi
- Các file đã refactor.
- Interface đã tạo.
- Những nơi còn dependency Mongo và vì sao còn giữ tạm.
