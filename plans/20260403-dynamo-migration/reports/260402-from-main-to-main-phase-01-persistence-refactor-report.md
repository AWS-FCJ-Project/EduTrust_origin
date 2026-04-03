# Phase 01 Report - Persistence Refactor

## Date: 2026-04-02
## Status: COMPLETED (Phase 01 core)

## 1. Files Created

### Persistence Layer
- `backend/src/persistence/__init__.py` - Module exports
- `backend/src/persistence/facade.py` - `PersistenceFacade` holding all domain repositories (lazy initialization)
- `backend/src/persistence/repositories/__init__.py` - Repository exports
- `backend/src/persistence/repositories/base.py` - `BaseRepository` with generic methods
- `backend/src/persistence/repositories/user_repository.py` - User repository (async via motor)
- `backend/src/persistence/repositories/class_repository.py` - Class repository
- `backend/src/persistence/repositories/exam_repository.py` - Exam repository
- `backend/src/persistence/repositories/submission_repository.py` - Submission repository
- `backend/src/persistence/repositories/violation_repository.py` - Violation repository
- `backend/src/persistence/repositories/conversation_repository.py` - Conversation repository
- `backend/src/persistence/repositories/otp_repository.py` - OTP repository (async)

## 2. Files Refactored

### `backend/src/main.py`
- Removed top-level MongoDB collection globals (`users_collection`, `classes_collection`, etc.)
- Lifespan now creates `PersistenceFacade` and stores in `app.state.persistence`
- `MongoClient` (sync) still created for `ConversationHandler` (Phase 01 conversation still uses Mongo)
- Removed `ExamHandler`/`ClassHandler` from app.state (replaced by persistence facade)

### `backend/src/auth/dependencies.py`
- Removed `from src.database import users_collection`
- `get_current_user()` now uses `request.app.state.persistence.users.get_by_email()`
- No more direct MongoDB access

### `backend/src/routers/auth/login.py`
- Removed `from src.database import classes_collection, users_collection`
- All DB operations go through `request.app.state.persistence`
- `login`: uses `persistence.users.get_by_email()` and `persistence.users.update_last_login()`
- `list_students`: uses `persistence.users.list_by_role()`
- `update_user`: uses `persistence.users.update()`, `persistence.classes.get_by_name_grade()`
- `delete_user`: uses `persistence.users.get_by_id()`, `persistence.classes.clear_homeroom_teacher()`, `persistence.classes.pull_subject_teacher()`, `persistence.users.delete()`
- `list_teachers`: uses `persistence.users.list_by_role()`, `persistence.classes.list_by_homeroom_teacher()`, `persistence.classes.list_all()`
- `list_admins`: uses `persistence.users.list_by_role()`

### `backend/src/routers/auth/register.py`
- Removed `from src.database import classes_collection, users_collection`
- All DB operations go through `request.app.state.persistence`
- `register`: uses `persistence.users.get_by_email()`, `persistence.classes.get_by_name_grade()`, `persistence.classes.insert_one()`, `persistence.users.insert_one()`
- `register_bulk`: uses same facade methods, iterates per-user for email check

### `backend/src/routers/auth/password.py`
- Removed `from src.database import users_collection`
- Uses `persistence.otps.save_otp()`, `persistence.otps.get_otp()`, `persistence.otps.delete_otp()`
- Uses `persistence.users.update_one()` for password hash update
- Inline OTP expiry check (was previously in otp_storage)

### `backend/src/auth/otp_storage.py`
- Replaced with a stub comment noting it now uses persistence facade
- Actual implementation is in `OtpRepository`

### `backend/src/routers/class_routes.py`
- Removed `from src.database import classes_collection`
- Removed `from src.database.class_handler import ClassHandler`
- All DB operations go through `request.app.state.persistence`
- Routes changed from sync `def` to `async def`
- Added helper functions `class_response_helper()` and `user_helper()` for formatting
- All CRUD operations now use persistence facade

### `backend/src/detection/violation_logger.py`
- Removed `from src.database import classes_collection, users_collection, violations_collection`
- Constructor now takes `persistence` instead of `base_path`
- `log_violation` uses `persistence.users.get_by_id()`, `persistence.exams.get_by_id()`, `persistence.classes.get_by_name_grade()`, `persistence.violations.upsert()`

## 3. Remaining MongoDB Dependencies (Phase 01 Acceptable)

### `exam_routes.py` + `ExamHandler`
- `exam_routes.py` still imports `from src.database.exam_handler import ExamHandler`
- `ExamHandler` uses pymongo directly
- **Reason**: ExamHandler contains complex business logic (submit_exam with score calculation, get_all_results_summary with aggregation pipeline, etc.) that cannot be trivially moved to repository calls in Phase 01
- **Plan**: Phase 03 will replace ExamHandler entirely with DynamoDB implementation
- **Note**: Routes no longer access collections directly; they go through ExamHandler methods

### `ConversationHandler`
- Still uses pymongo `MongoClient` directly
- **Reason**: Phase 01 leaves conversation handler as-is; Phase 03 will refactor
- Redis cache integration preserved

### `ObjectId.is_valid()` in routes
- Used for input ID validation in `class_routes.py`, `login.py`, `exam_routes.py`
- **Reason**: Simple string validation replacement would change behavior; acceptable for Phase 01
- **Plan**: Phase 03 will use DynamoDB-native ID validation

## 4. Interface Summary

### PersistenceFacade properties
- `users` → `UserRepository`
- `classes` → `ClassRepository`
- `exams` → `ExamRepository`
- `submissions` → `SubmissionRepository`
- `violations` → `ViolationRepository`
- `conversations` → `ConversationRepository`
- `otps` → `OtpRepository`

### Key UserRepository methods
- `get_by_email(email)`, `get_by_id(user_id)`, `create(doc)`, `update(id, fields)`, `delete(id)`
- `list_by_role(role)`, `find_users_by_ids(user_ids)`
- `list_students_by_class(name, grade)`, `list_students_by_class_id(class_id)`
- `list_available_students(class_name, grade)`, `count_students_in_class(name, grade)`
- `update_last_login(email)`

### Key ClassRepository methods
- `get_by_id(id)`, `get_by_name_grade(name, grade)`, `create(doc)`, `update(id, fields)`, `delete(id)`
- `list_all()`, `list_by_teacher(teacher_id)`, `list_by_homeroom_teacher(teacher_id)`
- `clear_homeroom_teacher(teacher_id)`, `pull_subject_teacher(teacher_id)`

## 5. Acceptance Criteria Check

| Criteria | Status |
|----------|--------|
| `rg -n "from src.database\|MongoClient\|motor\|pymongo" backend/src/routers` | Only `ExamHandler` import remains (acceptable for Phase 01) |
| Routes do not import collection globals | PASS - login, register, password, class_routes all clean |
| `main.py` uses facade | PASS - `app.state.persistence = PersistenceFacade(db)` |
| Unit tests can patch repository/facade | PASS - handlers get persistence from app.state |
| App compiles | PASS (type hints show only warnings, no blocking errors) |

## 6. Phase 01 Delivered

- ✅ Persistence facade + repositories created
- ✅ Auth routes (login, register, password) refactored to use facade
- ✅ Class routes refactored to use facade
- ✅ OTP storage refactored
- ✅ Violation logger refactored
- ✅ `main.py` bootstraps with facade
- ⚠️ Exam routes + ExamHandler remain (Phase 03)
- ⚠️ Conversation handler remains (Phase 03)
