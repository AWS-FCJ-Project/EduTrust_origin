# Kế hoạch tổng thể migrate backend sang DynamoDB

## 1. Mục tiêu
- Đưa toàn bộ backend sang chạy trên DynamoDB.
- Loại bỏ hoàn toàn MongoDB/DocumentDB khỏi steady state.
- Giữ nguyên public API hiện tại để frontend/client không phải đổi contract.
- Giữ nguyên ID public dưới dạng `string`.
- Giữ Redis cho conversation cache, không thay Redis bằng DynamoDB.

## 2. Hiện trạng codebase
- Repo hiện tại đang trộn 2 kiểu truy cập Mongo:
  - `motor` async qua `src.database` và `src.database.__init__`
  - `pymongo` sync qua `src.database.mongo_client.MongoClient`, `ClassHandler`, `ExamHandler`, `ConversationHandler`
- Các điểm phụ thuộc Mongo rõ nhất:
  - `backend/src/main.py`
  - `backend/src/auth/dependencies.py`
  - `backend/src/auth/otp_storage.py`
  - `backend/src/routers/auth/login.py`
  - `backend/src/routers/auth/register.py`
  - `backend/src/routers/auth/password.py`
  - `backend/src/routers/class_routes.py`
  - `backend/src/routers/exam_routes.py`
  - `backend/src/conversation/conversation_handler.py`
  - `backend/src/detection/violation_logger.py`
  - `backend/src/database/class_handler.py`
  - `backend/src/database/exam_handler.py`
  - `backend/src/database.py`
  - `backend/src/database/__init__.py`
  - `backend/src/database/mongo_client.py`
- Code hiện còn phụ thuộc mạnh vào:
  - `ObjectId`
  - query operators kiểu Mongo như `$or`, `$pull`, `$setOnInsert`, `$push`, `$slice`, aggregation pipeline
  - collection global import từ `src.database`

## 3. Target state
- Tạo một persistence layer thống nhất cho toàn bộ domain.
- App bootstrap chỉ khởi tạo:
  - DynamoDB persistence facade
  - Redis client
  - embedding model
- Các domain dùng repository/facade thay vì collection global:
  - users
  - classes
  - class_teacher_assignments
  - exams
  - submissions
  - violations
  - conversations
  - otps
- Xóa toàn bộ import/runtime reference đến:
  - `motor`
  - `pymongo`
  - `bson`
  - `MongoClient`
  - `MONGO_*`

## 4. Quy tắc triển khai
- Không đổi path endpoint.
- Không đổi request/response schema public.
- Không chuyển ID sang UUID/ULID trong phase này.
- Không thêm OpenSearch/vector database.
- Không triển khai single-table design.
- Chỉ dùng multi-table DynamoDB với key/GSI rõ ràng theo access pattern.
- Chỉ cho phép dual-write như trạng thái tạm trong migration, không giữ làm steady state.

## 5. Thứ tự phase bắt buộc
1. `phase-01-persistence-refactor.md`
2. `phase-02-dynamo-schema.md`
3. `phase-03-domain-migration.md`
4. `phase-03-exit-checklist.md`
5. `phase-04-lite-smoke-and-cutover-prep.md`
6. `phase-05-cutover-cleanup.md`

## 6. Tiêu chí hoàn thành cuối
- Tất cả endpoint auth, class, exam, conversation, OTP hoạt động với DynamoDB.
- Toàn repo không còn import hoặc runtime reference tới Mongo/DocumentDB.
- `backend/.env.example` không còn `MONGO_*`.
- `backend/pyproject.toml` không còn `motor`, `pymongo`.
- Terraform không còn outbound rule 27017 hoặc variable cho DocumentDB.
- Test suite cập nhật theo persistence mới.
- README và tài liệu vận hành phản ánh đúng trạng thái DynamoDB-only.

## 7. Cách dùng bộ kế hoạch này
- Mỗi phase phải được làm xong đầy đủ rồi mới chuyển phase tiếp theo.
- Claude Code phải tạo report sau từng phase vào thư mục `reports/`.
- Nếu trong quá trình thực hiện phát hiện khác biệt với codebase hiện tại, phải cập nhật lại phase file tương ứng trước khi tiếp tục.

## 8. Deliverable bắt buộc
- Code refactor + migrate.
- Test cập nhật.
- Terraform cập nhật.
- Tài liệu cập nhật.

## 9. Non-goals
- Không tối ưu hóa sâu cho throughput hoặc cost ở phase đầu.
- Không thiết kế event-driven architecture mới.
- Không thay đổi business rules hiện tại của auth/class/exam/conversation.

## 10. Risks cần theo dõi
- Auth flow bị gãy khi bỏ `users_collection` global.
- Exam summary sai nếu denormalized counters không cập nhật đúng.
- Conversation message order sai khi migrate từ Mongo list sang Dynamo item.
- Violation data bị lệch class/exam nếu enrich không thống nhất.
- Cleanup thiếu sót dẫn đến code path Mongo còn sót lại.
