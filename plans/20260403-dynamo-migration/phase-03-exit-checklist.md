# Phase 03 Exit Checklist - Hoàn tất migrate logic sang DynamoDB

## 1. Mục tiêu

- Tách phase 03 thành 2 phần rõ ràng:
- `Phase 03A`: code-only refactor hardening
- `Phase 03B`: runtime verification khi đã có Dynamo thật
- Ở trạng thái hiện tại, **ưu tiên chỉ làm 03A** vì chưa init Dynamo.
- Chưa làm cleanup Mongo toàn repo trong file này. Việc đó thuộc phase 5.
- Chưa làm backfill hoặc dual-write. Scope mới không cần.

## 2. Quy tắc thực thi cho Claude Code

- Hiện tại chỉ tập trung hoàn tất **Phase 03A - code-only**.
- Không được claim "phase 03 done" nếu chưa có `Phase 03B`.
- Không bắt đầu phase 4 lite khi chưa có Dynamo để boot và smoke test.
- Không làm phase 5 cleanup trong lúc đang sửa blocker phase 3, trừ khi một import Mongo cũ đang chặn code path mới.
- Giữ nguyên API public và response shape hiện tại.
- Không đổi business semantics nếu không có lý do bắt buộc.
- Khi phải chọn giữa "tương thích tạm" và "refactor sạch", ưu tiên hướng đơn giản, rõ contract, dễ verify.
- Mỗi module sửa xong phải đảm bảo:
- không shorthand variable mơ hồ
- không `unused import` hoặc `unused variable`
- pass `isort`
- pass `black`

## 3. Current Definition Of Done

### 3.1 Definition of done cho Phase 03A - code-only

- Interfaces giữa `main.py`, `PersistenceFacade`, repositories, handlers, routes đã nhất quán.
- Không còn shorthand variable gây mơ hồ trong code mới.
- Không còn `unused import`, `unused variable`, docstring/comment sai ngữ cảnh.
- Không còn `run_until_complete()` trong code path conversation mới.
- Không còn Mongo-shaped update contract bị để lẫn trong code path Dynamo.
- Mỗi module đã sửa phải clean theo formatter/import sorter của repo.

### 3.2 Definition of done cho Phase 03B - runtime

- `main.py` boot app với Dynamo persistence path.
- Không còn flow chính nào phụ thuộc Mongo để chạy.
- Password reset flow dùng contract OTP đúng và chạy được.
- Camera/violation logging không còn import symbol chết hoặc contract cũ.
- Repositories trả shape/type nhất quán đủ để routes và schemas hoạt động đúng.
- Smoke test cục bộ cho các flow chính pass.

## 4. Workstream A - Conversation contract

### Files cần sửa

- `backend/src/conversation/conversation_handler_dynamodb.py`
- `backend/src/conversation/conversation_handler.py`
- `backend/src/routers/conversation_routes.py`
- `backend/src/agent/unified_agent.py`
- `backend/src/schemas/unified_agent_schema.py`
- `backend/src/main.py`
- `backend/src/persistence/repositories/conversation_repository.py`

### Vấn đề hiện tại

- `DynamoDBConversationHandler` đang dùng `asyncio.get_event_loop().run_until_complete(...)`.
- `conversation_routes.py` vẫn annotate bằng `ConversationHandler` cũ.
- `unified_agent.py` và schema liên quan vẫn type theo handler Mongo cũ.
- repository delete conversation đang dùng key không đúng schema Dynamo.
- naming và import trong cụm file conversation chưa sạch cho code-only completion.

### Việc phải làm

1. Chốt contract mới cho conversation handler.
- Ưu tiên: để handler Dynamo có API giống handler cũ ở mức caller cần, nhưng implementation không dùng `run_until_complete`.
- Nếu route và orchestrator đã async-friendly, chuyển thẳng conversation path sang async-first.

2. Đồng bộ type imports.
- `conversation_routes.py` không còn import type của handler Mongo cũ.
- `unified_agent.py` và `schemas/unified_agent_schema.py` phải dùng type/protocol/interface hợp với handler mới.
- Không để type annotation kéo theo import runtime Mongo handler.

3. Sửa `ConversationRepository.delete_conversation()`.
- Key gửi vào `delete_item` phải đúng với key schema thật của table.
- Nếu cần kiểm tra owner:
  - hoặc read conversation trước, verify `user_id`, rồi mới delete
  - hoặc dùng condition expression hợp lệ
- Không nhét `user_id` vào `Key` nếu schema table không dùng field này làm sort key.

4. Sửa `get_conversation()` ownership behavior.
- Nếu route truyền `user_id`, repository/handler phải enforce ownership đúng.
- Không được trả conversation của user khác chỉ vì PK đúng.

5. Chốt persistence shape của conversation.
- `message_count` nên là số, không phải string nếu code tiêu dùng đang cần int.
- `created_at` và `updated_at` phải nhất quán kiểu dữ liệu.
- `messages` phải giữ đúng thứ tự.

6. Rà cache interaction.
- `get_context()`
- `add_message()`
- `delete_conversation()`
- cache invalidation/write-through phải khớp với persistence mới.

7. Dọn code style trong cụm conversation.
- đổi tên biến tắt khó hiểu nếu có
- xóa import không dùng
- comment/docstring không còn nhắc Mongo ở path mới
- format lại bằng `isort` và `black`

### Không được làm

- Không giữ `run_until_complete()` như giải pháp cuối.
- Không dùng thread hack để né event loop issue nếu không cần thiết.
- Không đổi endpoint path hay response schema.

### Tiêu chí xong

- `Phase 03A`: contract conversation sạch, không còn `run_until_complete`, không còn import/type kéo Mongo cũ, style module sạch.
- `Phase 03B`: conversation create/list/latest/get/delete chạy trên Dynamo path thật.

## 5. Workstream B - OTP và password reset contract

### Files cần sửa

- `backend/src/persistence/repositories/otp_repository.py`
- `backend/src/routers/auth/password.py`
- `backend/src/auth/otp_storage.py`
- `backend/tests/unit/test_otp_storage.py`

### Vấn đề hiện tại

- OTP repo và password route chưa thống nhất kiểu dữ liệu `expire_at`.
- `otp_storage.py` bị rỗng nhưng test vẫn import API cũ.

### Việc phải làm

1. Chốt contract của `OtpRepository`.
- `save_otp(email, purpose, otp, expire_seconds)`
- `get_otp(email, purpose, otp)`
- `delete_otp(email, purpose)`
- `delete_expired_otps()` hoặc no-op rõ ràng nếu dùng TTL

2. Chọn một chuẩn cho `expire_at`.
- Khuyến nghị: repository trả `datetime` hoặc route parse ISO string ngay khi nhận.
- Dù chọn hướng nào, contract phải được ghi rõ trong code comments ngắn hoặc test.

3. Đồng bộ `password.py`.
- `forgot-password` phải ghi OTP theo contract mới.
- `reset-password` phải verify expiry đúng cách.
- Update password qua repository theo shape update đúng, không giữ cú pháp Mongo như `{"$set": ...}` nếu repository không hỗ trợ.

4. Quyết định fate của `src/auth/otp_storage.py`.
- Hoặc xóa khỏi code path và sửa toàn bộ test/import liên quan.
- Hoặc biến nó thành compatibility wrapper mỏng gọi `OtpRepository`.

5. Cập nhật test OTP.
- Không còn patch `otp_collection`.
- Test dựa trên repository/facade hoặc fixture Dynamo client giả lập ở mức phù hợp.

6. Dọn code style.
- bỏ import không dùng
- tên biến rõ nghĩa
- không để module `otp_storage.py` ở trạng thái nửa chết nửa sống mà không nói rõ mục đích
- format lại file đã sửa bằng `isort` và `black`

### Không được làm

- Không để route giả định `expire_at` là datetime khi repo trả string.
- Không để module test import API đã chết.

### Tiêu chí xong

- `Phase 03A`: route và repo OTP có contract thống nhất, module sạch, test không import API chết.
- `Phase 03B`: forgot/reset password chạy đúng với Dynamo OTP repo.

## 6. Workstream C - Violation logger và camera flow

### Files cần sửa

- `backend/src/detection/violation_logger.py`
- `backend/src/detection/camera_service.py`
- `backend/src/routers/camera_routes.py`
- các điểm khởi tạo camera service nếu có

### Vấn đề hiện tại

- `camera_service.py` vẫn gọi `get_violation_logger()`.
- `violation_logger.py` chỉ còn class `ViolationLogger`.

### Việc phải làm

1. Chốt contract tạo logger.
- Khuyến nghị: constructor injection qua persistence, cùng style với các phần khác.
- Nếu camera service không tiện inject ngay, có thể giữ factory nhỏ nhưng factory phải trả logger mới đúng contract.

2. Đồng bộ mọi call site.
- Không còn import `get_violation_logger` nếu symbol này không tồn tại.
- Camera service phải dùng logger mới mà không cần Mongo client.

3. Sửa naming/comment cũ.
- `syncs evidence from S3 to MongoDB` trong docstring là sai với refactor hiện tại.
- Log message nên phản ánh Dynamo persistence path.

4. Verify repository contract với violation logger.
- `users.get_by_id()`
- `exams.get_by_id()`
- `classes.get_by_name_grade()`
- `violations.upsert()`
- các shape trả về phải đúng để logger enrich `class_id`, `subject`, `evidence_images`

5. Dọn code style.
- bỏ import/symbol chết
- sửa comment/docstring cũ nói về Mongo
- format các file liên quan bằng `isort` và `black`

### Tiêu chí xong

- `Phase 03A`: camera service không còn import symbol chết, logger contract rõ, module sạch.
- `Phase 03B`: violation logging chạy trên persistence mới.

## 7. Workstream D - Repository data contracts và type normalization

### Files cần sửa

- `backend/src/persistence/repositories/user_repository.py`
- `backend/src/persistence/repositories/class_repository.py`
- `backend/src/persistence/repositories/exam_repository.py`
- `backend/src/persistence/repositories/submission_repository.py`
- `backend/src/persistence/repositories/violation_repository.py`
- `backend/src/persistence/repositories/conversation_repository.py`
- `backend/src/persistence/dynamodb_client.py`
- `backend/src/persistence/repositories/base.py`

### Vấn đề hiện tại

- Nhiều repository đang ép số/bool thành string trước khi lưu.
- Một số method vẫn trả shape nửa-Mongo nửa-Dynamo.
- Một số repository methods còn stub hoặc trả rỗng mà routes có thể dựa vào.

### Việc phải làm

1. Chuẩn hóa quy tắc type.
- Numeric fields lưu và trả về dưới dạng số nếu business logic đang tiêu dùng là số.
- Boolean fields lưu và trả về dưới dạng bool.
- ID vẫn là string.
- Timestamp phải nhất quán.

2. Chuẩn hóa alias `_id`.
- Chỉ thêm alias ở layer cần tương thích API cũ.
- Không để mỗi method tự alias khác nhau theo kiểu ad-hoc.
- Nếu cần, gom helper ở base repository hoặc mapper riêng.

3. Rà các method đang stub.
- `find_one`
- `find_many`
- `update_one`
- `delete_one`
- `get_by_id`
- chỉ giữ method nào thật sự cần cho route hiện tại
- method được gọi bởi runtime path phải hoạt động đúng

4. Sửa cú pháp update không còn mang dấu vết Mongo.
- Không giả định repository nhận `$set`, `$inc`, pipeline kiểu Mongo nếu implementation không support.

5. Chuẩn hóa `DynamoDBClient`.
- serialize/deserialize phải tương thích type contract mới
- batch/write helper không để lại API sai hoặc nửa vời
- helper key PK/SK phải bám schema thật của phase 02

6. Dọn code style cho toàn bộ repository layer.
- bỏ shorthand kiểu `cls`, `cn`, `g`, `t` nếu không thực sự local và rõ nghĩa
- bỏ import không dùng
- bỏ biến khai báo rồi không dùng
- gom helper nếu đang lặp đơn giản
- chạy `isort` và `black` cho từng module đã sửa

### Không được làm

- Không tiếp tục string hóa số chỉ để “dễ lưu”.
- Không giữ method stub mà route vẫn gọi vào.

### Tiêu chí xong

- `Phase 03A`: route layer không phải tự vá contract cơ bản do repository trả về sai; module repository sạch và format chuẩn.
- `Phase 03B`: repositories đủ ổn định để dùng cho smoke test phase 4 lite.

## 8. Workstream E - Runtime path không còn phụ thuộc Mongo

### Files cần rà

- `backend/src/main.py`
- `backend/src/auth/dependencies.py`
- `backend/src/routers/auth/*.py`
- `backend/src/routers/class_routes.py`
- `backend/src/routers/exam_routes.py`
- `backend/src/routers/conversation_routes.py`
- `backend/src/routers/unified_agent_routes.py`
- `backend/src/streaming.py`

### Việc phải làm

1. Đảm bảo `main.py` chỉ boot path mới cho runtime chính.
- Không import thừa handler Mongo cũ nếu không cần.
- Không để import type/comment cũ làm người đọc hiểu sai state hệ thống.

2. Rà runtime imports.
- Các route và service hot path không được cần `src.database` để chạy.
- Nếu một file chỉ còn Mongo để phục vụ legacy không dùng đến, để phase 5 xóa.
- Nếu import Mongo cũ đang chặn runtime mới, phải bóc ngay trong phase 3.

3. Rà test/runtime env coupling.
- current runtime path không được yêu cầu `MONGO_*` mới chạy được.

4. Dọn code style ở bootstrap layer.
- bỏ import thừa
- bỏ comment kiểu `legacy, not used` nếu không còn giá trị
- rename biến ngắn/mơ hồ nếu có
- format file bằng `isort` và `black`

### Tiêu chí xong

- `Phase 03A`: runtime path chính không còn dependency code-level bắt buộc vào Mongo; bootstrap layer sạch.
- `Phase 03B`: app có thể boot logic chính bằng Dynamo path.

## 9. Code-only checks bắt buộc trước khi đóng Phase 03A

### 9.1 Static hygiene

- không `unused import`
- không `unused variable`
- không shorthand variable khó hiểu
- không comment/docstring sai ngữ cảnh Mongo ở path mới

### 9.2 Formatting

- chạy `isort` trên từng module đã sửa
- chạy `black` trên từng module đã sửa

### 9.3 Contract sanity

- không còn Mongo-style update payload nếu repo không support
- không còn import type kéo runtime path về Mongo
- không còn method stub nằm trên hot path mà route đang gọi

## 10. Smoke test bắt buộc trước khi đóng Phase 03B

### Auth

- login với user hợp lệ
- `/user-info`
- forgot password
- reset password

### Classes

- create class
- list classes theo admin
- get class detail
- add student
- remove student

### Exams

- create exam
- list exams theo teacher
- verify exam key
- submit exam
- get exam status
- get results summary

### Conversations

- create conversation
- add first user message
- list conversations
- get latest conversation
- get conversation detail
- delete conversation

### Violations

- log violation
- read violations theo class hoặc exam

## 11. Exit Gate

### Exit gate cho Phase 03A

- Tất cả blocker code-only ở workstream A-E đã xử lý.
- Static hygiene pass.
- `isort` và `black` pass trên các module đã sửa.
- Không còn mismatch contract lớn thấy được bằng static review.

### Exit gate cho Phase 03B

- Smoke test core flows pass.
- Không còn dependency Mongo bắt buộc cho runtime path chính.

## 12. Chỉ khi Phase 03B xong mới được chuyển sang phase 4 lite

Phase 4 lite không phải nơi sửa logic nền. Nó chỉ nên bao gồm:

- apply table/index
- seed tối thiểu nếu cần
- smoke test toàn hệ thống
- xác nhận app boot trong cấu hình Dynamo-first

## 13. Report Claude Code phải ghi sau khi hoàn thành

- Những file đã sửa
- Blocker nào đã được đóng
- Contract nào đã được chốt
- Smoke test nào đã pass
- Mongo dependencies nào còn lại nhưng chỉ thuộc phase 5
- Unresolved questions
