# Next Step After Second Review - Test Surface Alignment và Status Correction

## Date: 2026-04-03
## Scope: Phase 03A code-only

## Summary

Review lần này cho thấy cụm `UnifiedAgent` và conversation async path đã tiến đúng hướng, nhưng vẫn còn một nhóm việc chưa chốt:

- OTP compatibility đã được vá ở mức module, nhưng test surface chưa được cập nhật theo implementation mới
- `otp_storage.py` đang phụ thuộc trực tiếp vào `src.main.app`, làm module khó test và kéo side effect không cần thiết
- report `phase-03-completion` đang claim mạnh hơn trạng thái thực tế của code/test hiện tại

## Step 1 - Sửa test surface của OTP cho đúng implementation hiện tại

### Files cần sửa

- `backend/tests/unit/test_otp_storage.py`
- nếu cần: tạo test mới ở layer repository hoặc facade

### Vấn đề hiện tại

- test vẫn patch `src.auth.otp_storage.otp_collection`
- symbol `otp_collection` không còn tồn tại trong module mới
- test đang bám contract Mongo cũ, không còn phản ánh behavior thật

### Việc phải làm

1. Viết lại test OTP theo contract hiện tại:
- `save_otp(email, otp, purpose, expire_seconds)`
- `verify_otp(email, otp, purpose)`
- `cleanup_expired_otps()`

2. Patch đúng dependency hiện tại.
- nếu vẫn giữ wrapper `otp_storage.py`, patch `_get_otp_repo()` hoặc patch repo object mà wrapper dùng
- không patch `otp_collection` nữa

3. Kiểm tra đủ các case:
- OTP không tồn tại
- OTP hết hạn
- OTP hợp lệ
- OTP hợp lệ với naive datetime nếu module vẫn support
- save gọi đúng repo method
- cleanup là no-op hoặc gọi đúng repo cleanup method

### Exit criteria

- test OTP phản ánh implementation hiện tại, không còn assumptions Mongo cũ

## Step 2 - Giảm coupling của `otp_storage.py` với `src.main`

### Files cần sửa

- `backend/src/auth/otp_storage.py`

### Vấn đề hiện tại

- `_get_otp_repo()` import `from src.main import app`
- điều này kéo module helper sang phụ thuộc app global
- unit test và import đơn lẻ có thể bị side effect không cần thiết

### Việc phải làm

Chọn một trong hai hướng:

#### Hướng A - giữ compatibility wrapper nhưng cho phép inject

- thêm cách set repo/provider trong test
- `_get_otp_repo()` chỉ fallback về `src.main.app` nếu chưa inject
- test dùng injected repo giả

#### Hướng B - bỏ helper global, chuyển callers sang repo trực tiếp

- nếu không còn caller nào thực sự cần `otp_storage.py`, đánh dấu module là legacy compatibility tạm thời
- đơn giản hóa hoặc xóa hẳn khi phase 5 cleanup

### Khuyến nghị

- nếu mục tiêu là giữ Phase 03A gọn và ít ripple nhất, dùng **Hướng A**

### Exit criteria

- `otp_storage.py` test được mà không cần boot `src.main`

## Step 3 - Chỉnh lại completion report cho đúng mức certainty

### Files cần sửa

- `plans/20260403-dynamo-migration/reports/260403-from-main-to-refactor-database-operation-phase-03-completion-report.md`

### Vấn đề hiện tại

- report đang claim `PHASE 03A CODE-ONLY COMPLETE`
- nhưng test OTP hiện chưa align với implementation mới
- phần “static hygiene pass” và “all blockers resolved” đang mạnh hơn bằng chứng đang có

### Việc phải làm

1. Hạ status nếu cần.
- ví dụ: `PHASE 03A MOSTLY COMPLETE — remaining test-surface alignment`

2. Ghi rõ blocker còn lại:
- OTP test surface chưa sync
- dependency conflict ở `pyproject.toml` vẫn chặn runtime verification

3. Không claim pass nếu chưa có bằng chứng tương ứng.

### Exit criteria

- report phản ánh đúng codebase state và không overclaim

## Step 4 - Rà lại nhóm file vừa sửa bằng hygiene pass

### Files ưu tiên

- `backend/src/auth/otp_storage.py`
- `backend/tests/unit/test_otp_storage.py`
- `plans/.../phase-03-completion-report.md`

### Bắt buộc

- không `unused import`
- không `unused variable`
- không shorthand variable mơ hồ
- `isort`
- `black`

## Thứ tự thực hiện khuyên dùng

1. Rewrite `test_otp_storage.py`
2. Refactor nhẹ `otp_storage.py` để testable hơn
3. Chỉnh lại completion report
4. Hygiene pass trên cụm file vừa đụng

## Deliverable Claude Code phải ghi

- test OTP đã được cập nhật theo contract nào
- `otp_storage.py` hiện đang theo Hướng A hay Hướng B
- completion report đã chỉnh gì
- unresolved questions

## Unresolved Questions

- Có muốn giữ `otp_storage.py` lâu hơn như compatibility layer, hay chỉ là cầu nối tạm thời trước phase 5?
- Nếu giữ wrapper, có chấp nhận thêm cơ chế inject repo riêng cho test không?
