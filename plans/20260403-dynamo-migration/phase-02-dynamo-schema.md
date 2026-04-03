# Phase 02 - Khóa thiết kế DynamoDB

## 1. Mục tiêu
- Chốt schema DynamoDB theo access pattern thực tế.
- Không để implementation phase 3 tự quyết định key/GSI.
- Tránh tình trạng code viết xong mới phát hiện query không support được.

## 2. Quyết định kiến trúc
- Dùng `multi-table design`.
- Không dùng `single-table design`.
- Không dùng scan cho hot path.
- Cho phép denormalization có kiểm soát để giảm aggregation/query fan-out.

## 3. Bảng và key design

### 3.1 `users`
- PK: `user_id`
- Attributes chính:
  - `email`
  - `hashed_password`
  - `is_verified`
  - `name`
  - `role`
  - `class_id`
  - `class_name`
  - `grade`
  - `subjects`
  - `created_at`
  - `last_login`
- GSI:
  - `email-index` với PK `email`
  - `role-index` với PK `role`, SK `name` hoặc `user_id`
  - `class-id-index` với PK `class_id`, SK `name` hoặc `user_id`

### 3.2 `classes`
- PK: `class_id`
- Attributes chính:
  - `name`
  - `grade`
  - `school_year`
  - `homeroom_teacher_id`
  - `subject_teachers`
  - `status`
  - `student_count`
  - `lookup_key = "{grade}#{name}"`
- GSI:
  - `class-lookup-index` với PK `lookup_key`
  - `homeroom-teacher-index` với PK `homeroom_teacher_id`

### 3.3 `class_teacher_assignments`
- PK: `teacher_id`
- SK: `class_id#subject`
- Attributes chính:
  - `class_id`
  - `teacher_id`
  - `subject`
  - `class_name`
  - `grade`
- GSI:
  - `class-id-index` với PK `class_id`, SK `teacher_id#subject`

### 3.4 `exams`
- PK: `exam_id`
- Attributes chính:
  - `title`
  - `description`
  - `subject`
  - `exam_type`
  - `teacher_id`
  - `class_id`
  - `class_name`
  - `grade`
  - `start_time`
  - `end_time`
  - `duration`
  - `secret_key`
  - `questions`
  - `submission_count`
  - `score_total`
  - `highest_score`
  - `violation_total`
- GSI:
  - `teacher-index` với PK `teacher_id`, SK `start_time`
  - `class-index` với PK `class_id`, SK `start_time`

### 3.5 `submissions`
- PK: `exam_id`
- SK: `student_id`
- Attributes chính:
  - `submitted_at`
  - `score`
  - `correct_count`
  - `total_questions`
  - `status`
  - `violation_count`
- GSI:
  - `student-index` với PK `student_id`, SK `submitted_at`

### 3.6 `violations`
- PK: `exam_id`
- SK: `student_id`
- Attributes chính:
  - `class_id`
  - `subject`
  - `type`
  - `timestamp`
  - `violation_time`
  - `evidence_images`
  - `metadata`
  - `created_at`
  - `updated_at`
- GSI:
  - `class-time-index` với PK `class_id`, SK `violation_time`
  - `student-index` với PK `student_id`, SK `violation_time`

### 3.7 `conversations`
- PK: `conversation_id`
- Attributes chính:
  - `user_id`
  - `title`
  - `messages`
  - `message_count`
  - `last_message_preview`
  - `created_at`
  - `updated_at`
- GSI:
  - `user-updated-index` với PK `user_id`, SK `updated_at`

### 3.8 `otps`
- PK: `otp_key = "{email}#{purpose}"`
- Attributes chính:
  - `email`
  - `purpose`
  - `otp`
  - `created_at`
  - `expire_at`
  - `expire_at_epoch`
- TTL:
  - `expire_at_epoch`

## 4. Access pattern map bắt buộc

### Auth/User
- Login theo email -> `users.email-index`
- User info theo id -> `users.PK`
- List teachers/students/admins -> `users.role-index`
- Students by class -> `users.class-id-index`

### Class
- Resolve class theo `name + grade` -> `classes.class-lookup-index`
- Class detail theo id -> `classes.PK`
- Homeroom classes theo teacher -> `classes.homeroom-teacher-index`
- Subject teacher classes -> `class_teacher_assignments.PK`

### Exam
- Exam detail theo id -> `exams.PK`
- Exams theo teacher -> `exams.teacher-index`
- Exams theo class -> `exams.class-index`
- Submissions theo exam -> `submissions.PK`
- Results theo student -> `submissions.student-index`

### Violation
- Upsert violation theo `(exam_id, student_id)` -> `violations.PK + SK`
- Violations theo class -> `violations.class-time-index`

### Conversation
- Conversation detail theo id -> `conversations.PK`
- List/latest theo user -> `conversations.user-updated-index`

### OTP
- Save/verify/delete OTP -> `otps.PK`

## 5. Denormalization bắt buộc
- `classes.student_count`
- `exams.submission_count`
- `exams.score_total`
- `exams.highest_score`
- `exams.violation_total`
- `conversations.last_message_preview`
- `classes.lookup_key`

## 6. Các query Mongo phải được thay thế bằng gì
- `$or` teacher/class lookup -> GSI hoặc assignment table
- `$pull` subject teacher remove -> delete item ở `class_teacher_assignments` + rebuild field `subject_teachers`
- `$setOnInsert` -> conditional write
- `$push/$slice` messages -> read-modify-write hoặc conditional update conversation item
- aggregation pipeline summary -> denormalized counters trên exam

## 7. Terraform/infra deliverable
- Tạo DynamoDB tables và GSIs tương ứng.
- Tạo TTL cho `otps`.
- Cấp IAM permission cho ứng dụng:
  - `GetItem`
  - `PutItem`
  - `UpdateItem`
  - `DeleteItem`
  - `Query`
  - `BatchWriteItem`
  - `BatchGetItem`
  - `TransactWriteItems`
- Không thêm resource DocumentDB mới.

## 8. Acceptance criteria
- Mỗi endpoint/domain đều có path query rõ ràng, không còn “scan rồi filter”.
- Không có hot path nào phụ thuộc `Scan`.
- Thiết kế đủ để implement phase 3 mà không cần quyết định lại.

## 9. Report phải ghi
- Final schema tables.
- GSIs và lý do tồn tại.
- Access pattern map.
- Những denormalized fields đã khóa.
