# Phase 03 - Migrate logic theo domain sang DynamoDB

## 1. Mục tiêu
- Chuyển toàn bộ business flow từ Mongo abstraction sang Dynamo repositories.
- Giữ nguyên endpoint, request schema, response schema.
- Không để phase này tiếp tục dùng collection global hoặc logic Mongo cũ.

## 2. Điều kiện trước khi bắt đầu
- Phase 01 đã xong: route/service đã đi qua facade/repository.
- Phase 02 đã xong: schema Dynamo và access pattern đã khóa.

## 3. Domain breakdown

### 3.1 Auth và users
#### Files chính
- `backend/src/auth/dependencies.py`
- `backend/src/routers/auth/login.py`
- `backend/src/routers/auth/register.py`
- `backend/src/routers/auth/password.py`
- `backend/src/schemas/auth_schemas.py`
- persistence user repository files

#### Việc phải làm
- Login lookup qua `users.email-index`.
- `get_current_user()` lấy user qua repository.
- Register user mới ghi vào `users`.
- Nếu student register với `class_name + grade`, resolve class qua `classes.class-lookup-index`.
- Update/delete user không dùng `ObjectId`.
- List students/teachers/admins qua `users.role-index`.
- Giữ nguyên `user_helper()` shape output.

#### Bẫy kỹ thuật
- Delete teacher phải đồng thời dọn assignment records.
- Nếu class chưa tồn tại trong register/update flow, phải giữ nguyên business rule hiện tại: auto-create class inactive.

### 3.2 OTP
#### Files chính
- `backend/src/auth/otp_storage.py`

#### Việc phải làm
- Save OTP vào `otps` table.
- Verify OTP theo `otp_key`.
- Delete OTP sau verify.
- Cleanup expired dựa trên TTL hoặc delete thủ công khi cần.

#### Bẫy kỹ thuật
- Dynamo TTL không xóa item ngay lập tức, nên verify phải tự check `expire_at`.

### 3.3 Classes
#### Files chính
- `backend/src/database/class_handler.py` hoặc lớp thay thế
- `backend/src/routers/class_routes.py`
- `backend/src/schemas/school_schemas.py`

#### Việc phải làm
- CRUD class qua `classes` table.
- Resolve teacher-class relationship qua:
  - `homeroom_teacher_id`
  - `class_teacher_assignments`
- `student_count` cập nhật ở write path khi add/remove student hoặc register/delete student.
- `get_students` query `users.class-id-index`.
- `get_available_students` không dùng logic Mongo `$or/$ne`; phải query users theo role và filter rõ theo `class_id`.

#### Bẫy kỹ thuật
- Hiện code cũ lưu student theo `class_name + grade`; phase này nên chuẩn hóa thêm `class_id` nhưng vẫn giữ `class_name/grade` để không phá response.

### 3.4 Exams và submissions
#### Files chính
- `backend/src/database/exam_handler.py` hoặc lớp thay thế
- `backend/src/routers/exam_routes.py`
- `backend/src/schemas/exam_schemas.py`

#### Việc phải làm
- Create exam vào `exams`.
- List exams theo teacher/class/admin từ GSI.
- Verify key qua `exams.PK`.
- Submit exam qua `TransactWriteItems` hoặc conditional sequence:
  - chỉ insert submission nếu chưa tồn tại
  - update counters trên exam
  - delete violation item nếu status completed
- `get_student_results()` đọc từ `submissions.student-index`, sau đó hydrate exam info.
- `get_all_results_summary()` đọc trực tiếp từ counters trên `exams`, không aggregate submissions.

#### Bẫy kỹ thuật
- Không được cho phép double submit.
- `highest_score` và `score_total` phải được cập nhật đúng ngay tại write path.
- Nếu transaction không dùng được trong local test, phải có wrapper để mock được.

### 3.5 Violations
#### Files chính
- `backend/src/detection/violation_logger.py`
- exam/class services phần read violation

#### Việc phải làm
- Upsert violation theo `(exam_id, student_id)`.
- Enrich class_id, subject, evidence_images tại thời điểm ghi.
- Query violation theo class qua `class-time-index`.
- Query violation theo exam qua PK.

#### Bẫy kỹ thuật
- Không để read path phải tự sửa dữ liệu hàng loạt như code cũ đang làm.

### 3.6 Conversations
#### Files chính
- `backend/src/conversation/conversation_handler.py`
- `backend/src/conversation/conversation_cache.py`
- `backend/src/routers/conversation_routes.py`
- `backend/src/schemas/conversation_schema.py`

#### Việc phải làm
- Create conversation vào `conversations`.
- List/latest qua `user-updated-index`.
- Get conversation theo PK, scope theo `user_id` nếu cần.
- Delete conversation theo PK và owner.
- Append message:
  - giữ message order
  - tăng `message_count`
  - update `updated_at`
  - update `last_message_preview`
  - cập nhật title từ first user message giống behavior cũ
- Redis cache giữ nguyên, chỉ đổi nguồn persistence.
- Search conversation vẫn dùng embedding ở app layer trên title list hiện có.

#### Bẫy kỹ thuật
- Append message kiểu list trong Dynamo cần kiểm soát race condition.
- Nếu chưa có optimistic version, phải đảm bảo write path không silently mất message.

## 4. Thứ tự thực hiện khuyên dùng trong phase này
1. Users + auth dependency
2. OTP
3. Classes
4. Exams + submissions
5. Violations
6. Conversations

## 5. Acceptance criteria
- Không còn repository/domain logic nào dùng Mongo-specific API.
- Tất cả route đang gọi repository Dynamo.
- Public response schema không đổi.
- Không còn `ObjectId` trong auth/class/exam/conversation flow.

## 6. Report phải ghi
- Domain nào đã migrate xong.
- Domain nào còn fallback tạm.
- Những business rule giữ nguyên từ code cũ.
