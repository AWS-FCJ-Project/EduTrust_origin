# Phase 05 - Cutover sang DynamoDB và cleanup Mongo

## 1. Mục tiêu
- Chuyển read source chính sang DynamoDB.
- Sau khi ổn định, xóa hoàn toàn Mongo khỏi codebase và infra.

## 2. Bước cutover

### 2.1 Flip read source
- Chuyển config mode từ `dual_write` sang `dynamo`.
- Tất cả read path phải lấy từ Dynamo.
- Giữ Mongo write thêm ngắn hạn chỉ nếu cần rollback window rõ ràng.

### 2.2 Stabilization window
- Theo dõi:
  - login success rate
  - class/exam list correctness
  - exam submit correctness
  - conversation latest/get correctness
- Nếu lỗi xảy ra:
  - rollback config về `dual_write` hoặc `mongo`
  - không rollback bằng sửa dữ liệu tay trước khi có parity result

### 2.3 Remove Mongo write
- Sau stabilization window, tắt hẳn Mongo write.

## 3. Cleanup code bắt buộc
- Xóa hoặc thay thế hoàn toàn:
  - `backend/src/database.py`
  - `backend/src/database/__init__.py`
  - `backend/src/database/mongo_client.py`
  - Mongo-specific handler code cũ trong class/exam/conversation layer
- Xóa dependency:
  - `motor`
  - `pymongo`
  - `bson`
- Xóa env:
  - `MONGO_URI`
  - `MONGO_USERNAME`
  - `MONGO_PASSWORD`
  - `MONGO_PORT`
  - `MONGO_DB_NAME`
- Cập nhật `backend/src/app_config.py` sang `DYNAMODB_*`.
- Cập nhật `backend/.env.example`.

## 4. Cleanup infra bắt buộc
- Terraform:
  - bỏ variable DocumentDB egess
  - bỏ outbound 27017
  - thêm DynamoDB tables và IAM policy
- CI/CD:
  - bỏ step hoặc env liên quan Mongo nếu có
  - thêm validate cho config Dynamo nếu cần

## 5. Cleanup tests
- Xóa/đổi test đang patch Mongo collection global.
- Xóa test phụ thuộc `ObjectId`, `motor`, `pymongo`.
- Update fixture env từ Mongo sang Dynamo config.
- Ưu tiên patch repository/facade thay vì patch collection/raw client.

## 6. Cleanup docs
- Cập nhật:
  - `README.md`
  - deployment docs liên quan infra
  - biến môi trường mẫu
  - hướng dẫn local dev/test

## 7. Lệnh kiểm tra bắt buộc sau cleanup
- Search codebase:
  - `rg -n "motor|pymongo|bson|MongoClient|MONGO_" backend .github README.md`
- Chạy test suite backend.
- Chạy Terraform validate/fmt check.

## 8. Acceptance criteria
- App chỉ dùng DynamoDB cho persistence.
- Toàn repo không còn import/reference Mongo/DocumentDB.
- Tests pass với config Dynamo-only.
- Infra không còn rule hoặc variable dành cho DocumentDB.
- README và `.env.example` phản ánh đúng trạng thái mới.

## 9. Report phải ghi
- Thời điểm flip sang Dynamo.
- Kết quả post-cutover verification.
- Những file/code/dependency đã xóa.
- Kết quả grep xác nhận không còn Mongo reference.
