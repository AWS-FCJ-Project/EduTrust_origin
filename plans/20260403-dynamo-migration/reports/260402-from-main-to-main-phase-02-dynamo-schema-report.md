# Phase 02 Report - DynamoDB Schema Design

## Date: 2026-04-02
## Status: COMPLETED

## 1. DynamoDB Tables Created (`dynamodb.tf`)

### Table: users
- **PK**: `user_id` (String)
- **Attributes**: email, hashed_password, is_verified, name, role, class_id, class_name, grade, subjects, created_at, last_login
- **GSI: email-index** (PK: email) — Login lookup
- **GSI: role-index** (PK: role, SK: user_id) — List teachers/students/admins
- **GSI: class-id-index** (PK: class_id, SK: user_id) — List students by class

### Table: classes
- **PK**: `class_id` (String)
- **Attributes**: name, grade, school_year, homeroom_teacher_id, subject_teachers, status, student_count, lookup_key
- **GSI: class-lookup-index** (PK: lookup_key = "{grade}#{name}") — Resolve class by name+grade
- **GSI: homeroom-teacher-index** (PK: homeroom_teacher_id) — List homeroom classes by teacher

### Table: class_teacher_assignments
- **PK**: `teacher_id` (String)
- **SK**: `assignment_key` = "{class_id}#{subject}" (String)
- **Attributes**: class_id, teacher_id, subject, class_name, grade
- **GSI: class-id-index** (PK: class_id, SK: assignment_key) — Find all teachers of a class

### Table: exams
- **PK**: `exam_id` (String)
- **Attributes**: title, description, subject, exam_type, teacher_id, class_id, class_name, grade, start_time, end_time, duration, secret_key, questions, submission_count, score_total, highest_score, violation_total
- **GSI: teacher-index** (PK: teacher_id, SK: start_time) — List exams by teacher
- **GSI: class-index** (PK: class_id, SK: start_time) — List exams by class

### Table: submissions
- **PK**: `exam_id` (String)
- **SK**: `student_id` (String)
- **Attributes**: submitted_at, score, correct_count, total_questions, status, violation_count
- **GSI: student-index** (PK: student_id, SK: submitted_at) — List results by student

### Table: violations
- **PK**: `exam_id` (String)
- **SK**: `student_id` (String)
- **Attributes**: class_id, subject, type, timestamp, violation_time, evidence_images, metadata, created_at, updated_at
- **GSI: class-time-index** (PK: class_id, SK: violation_time) — List violations by class
- **GSI: student-index** (PK: student_id, SK: violation_time) — List violations by student

### Table: conversations
- **PK**: `conversation_id` (String)
- **Attributes**: user_id, title, messages (list), message_count, last_message_preview, created_at, updated_at
- **GSI: user-updated-index** (PK: user_id, SK: updated_at) — List/latest conversations by user

### Table: otps
- **PK**: `otp_key` = "{email}#{purpose}" (String)
- **Attributes**: email, purpose, otp, created_at, expire_at, expire_at_epoch
- **TTL**: `expire_at_epoch` (enabled) — Automatic OTP expiration

## 2. Access Pattern Map

| Operation | DynamoDB Path |
|-----------|---------------|
| Login by email | `users.email-index` Query(email=) |
| User by ID | `users.PK` GetItem |
| List teachers/students | `users.role-index` Query(role=) |
| List students by class | `users.class-id-index` Query(class_id=) |
| Resolve class by name+grade | `classes.class-lookup-index` Query(lookup_key=) |
| Class detail by ID | `classes.PK` GetItem |
| Homeroom classes by teacher | `classes.homeroom-teacher-index` Query(homeroom_teacher_id=) |
| Exam detail by ID | `exams.PK` GetItem |
| Exams by teacher | `exams.teacher-index` Query(teacher_id=) |
| Exams by class | `exams.class-index` Query(class_id=) |
| Submissions by exam | `submissions.PK` Query(exam_id=) |
| Results by student | `submissions.student-index` Query(student_id=) |
| Upsert violation | `violations.PK+SK` PutItem |
| Violations by class | `violations.class-time-index` Query(class_id=) |
| Conversation by ID | `conversations.PK` GetItem |
| List conversations by user | `conversations.user-updated-index` Query(user_id=) |
| Save/verify OTP | `otps.PK` GetItem/PutItem/DeleteItem |

## 3. Denormalized Fields (Locked)

- `classes.student_count` — Updated at write path when add/remove student
- `exams.submission_count` — Updated on submit
- `exams.score_total` — Updated on submit
- `exams.highest_score` — Updated on submit
- `exams.violation_total` — Updated on violation upsert
- `conversations.last_message_preview` — Updated on append_message
- `classes.lookup_key` = "{grade}#{name}"

## 4. Terraform Changes

### New file: `dynamodb.tf`
- All 8 DynamoDB tables with GSIs
- TTL enabled on `otps` table
- PAY_PER_REQUEST billing (on-demand)
- Consistent tags

### Updated: `main.tf`
- Added DynamoDB gateway VPC endpoint (private subnets)
- Added `aws_iam_role_policy: backend_dynamodb` with full DynamoDB permissions

### Updated: `outputs.tf`
- Added ARNs for all 8 DynamoDB tables

### Updated: `app_config.py`
- Added DynamoDB config: `DYNAMODB_TABLE_PREFIX`, `DYNAMODB_REGION`, `DYNAMODB_ENDPOINT`

## 5. MongoDB Query Replacements

| MongoDB Operation | DynamoDB Replacement |
|-------------------|---------------------|
| `$or` teacher/class lookup | GSI or assignment table |
| `$pull` subject teacher remove | Delete item from `class_teacher_assignments` |
| `$setOnInsert` | Conditional write with `if_not_exists()` |
| `$push/$slice` messages | Read-modify-write or update conversation item |
| Aggregation pipeline summary | Denormalized counters on `exams` |
| `count_documents` | `Scan` with filter (acceptable for small sets) |

## 6. Non-Goals Confirmed

- No single-table design used (multi-table per plan)
- No OpenSearch/vector database added
- No UUID/ULID migration for IDs (kept as String)
- No scan for hot paths (all access patterns use PK or GSI)

## 7. Acceptance Criteria Check

| Criteria | Status |
|----------|--------|
| Each endpoint/domain has clear query path | PASS - all access patterns mapped to PK/GSI |
| No hot path depends on Scan | PASS |
| Design sufficient for Phase 03 without redesign | PASS |
| IAM permissions include all DynamoDB operations | PASS |
| TTL on otps table | PASS |

## 8. Phase 02 Delivered

- ✅ All 8 DynamoDB tables defined with GSIs
- ✅ Access pattern map documented
- ✅ Denormalized fields locked
- ✅ Terraform DynamoDB resources created
- ✅ IAM policy for DynamoDB added
- ✅ VPC endpoint for DynamoDB added
- ✅ Outputs added for all table ARNs
- ✅ `app_config.py` updated with DynamoDB env vars
