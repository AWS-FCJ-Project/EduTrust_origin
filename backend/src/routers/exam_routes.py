import asyncio
import secrets
from datetime import datetime, timezone
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.dependencies import get_current_user
from src.schemas.exam_schemas import (
    ExamCreate,
    ExamCreateResponse,
    ExamDeleteResponse,
    ExamKeyVerify,
    ExamRegenerateKeyResponse,
    ExamResultSummary,
    ExamResultSummaryList,
    ExamSecretKeyResponse,
    ExamStatusResponse,
    ExamSubmission,
    ExamSubmissionResponse,
    ExamSubmissionSummary,
    ExamUpdate,
    ExamUpdateResponse,
    ExamVerifyKeyResponse,
    ExamViolation,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


def get_persistence(request: Request):
    """Get persistence facade from app state."""
    return request.app.state.persistence


def exam_response_helper(exam: dict, include_secret: bool = False) -> dict:
    """Format exam document for API response."""
    result = {
        "id": exam.get("exam_id") or exam.get("id"),
        "title": exam.get("title", ""),
        "description": exam.get("description"),
        "subject": exam.get("subject", ""),
        "exam_type": exam.get("exam_type", "15-minute quiz"),
        "teacher_id": exam.get("teacher_id", ""),
        "class_id": exam.get("class_id", ""),
        "start_time": exam.get("start_time", ""),
        "end_time": exam.get("end_time", ""),
        "duration": exam.get("duration", 60),
        "has_secret_key": bool(exam.get("secret_key")),
        "questions": exam.get("questions", []),
    }
    if include_secret:
        result["secret_key"] = exam.get("secret_key")
    return result


async def can_create_exam(
    persistence, role: str, user_id: str, class_id: str
) -> tuple[bool, dict | None]:
    """Check if user can create exam in class."""
    if role == "admin":
        cls = await persistence.classes.get_by_id(class_id)
        return bool(cls), cls

    if role != "teacher":
        return False, None

    cls = await persistence.classes.get_by_id(class_id)
    if not cls:
        return False, None

    is_homeroom = cls.get("homeroom_teacher_id") == user_id
    is_subject = any(
        t.get("teacher_id") == user_id
        for t in cls.get("subject_teachers", [])
        if isinstance(t, dict)
    )
    return bool(is_homeroom or is_subject), cls


async def can_access_exam(
    persistence, role: str, user_id: str, exam_id: str
) -> tuple[bool, dict | None]:
    """Check if user can access exam."""
    exam = await persistence.exams.get_by_id(exam_id)
    if not exam:
        return False, None

    if role == "admin":
        return True, exam

    if role == "teacher":
        if exam.get("teacher_id") == user_id:
            return True, exam
        cls = await persistence.classes.get_by_id(exam.get("class_id", ""))
        if cls:
            is_homeroom = cls.get("homeroom_teacher_id") == user_id
            is_subject = any(
                t.get("teacher_id") == user_id
                for t in cls.get("subject_teachers", [])
                if isinstance(t, dict)
            )
            if is_homeroom or is_subject:
                return True, exam

    if role == "student":
        # Student accesses via class - they need to match the class
        user = await persistence.users.get_by_id(user_id)
        if user:
            student_class_name = user.get("class_name", "")
            student_grade = user.get("grade")

            # Prefer class_id match (works even if exam lacks denormalized class_name/grade)
            try:
                cls = await persistence.classes.get_by_name_grade(
                    student_class_name, int(student_grade)
                )
            except Exception:
                cls = None
            if (
                cls
                and cls.get("class_id")
                and exam.get("class_id") == cls.get("class_id")
            ):
                return True, exam

            # Legacy fallback: compare denormalized class_name/grade
            exam_class_name = exam.get("class_name", "")
            exam_grade = exam.get("grade")
            if student_class_name == exam_class_name and str(student_grade) == str(
                exam_grade
            ):
                return True, exam

    return False, exam


async def can_modify_exam(
    persistence, role: str, user_id: str, exam_id: str
) -> tuple[bool, dict | None]:
    """Check if user can modify/delete exam."""
    if role == "admin":
        exam = await persistence.exams.get_by_id(exam_id)
        return True, exam

    exam = await persistence.exams.get_by_id(exam_id)
    if not exam:
        return False, None

    if role != "teacher":
        return False, exam

    if exam.get("teacher_id") == user_id:
        return True, exam

    cls = await persistence.classes.get_by_id(exam.get("class_id", ""))
    if cls:
        is_homeroom = cls.get("homeroom_teacher_id") == user_id
        is_subject = any(
            t.get("teacher_id") == user_id
            for t in cls.get("subject_teachers", [])
            if isinstance(t, dict)
        )
        if is_homeroom or is_subject:
            return True, exam

    return False, exam


@router.post("", response_model=ExamCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_data: ExamCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamCreateResponse:
    """Create a new exam (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=403, detail="Only teachers or admins can create exams"
        )

    allowed, class_info = await can_create_exam(
        persistence, role, user_id, exam_data.class_id
    )
    if not allowed:
        if not class_info:
            raise HTTPException(status_code=404, detail="Class not found")
        raise HTTPException(status_code=403, detail="You do not teach this class")

    secret_key = exam_data.secret_key
    if not secret_key:
        secret_key = secrets.token_hex(3).upper()
    else:
        secret_key = str(secret_key).strip().upper()

    def _to_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    teacher_id = user_id
    # If admin creates an exam, assign teacher_id to homeroom teacher (if present) so it shows in teacher views.
    if role == "admin" and class_info and class_info.get("homeroom_teacher_id"):
        teacher_id = class_info.get("homeroom_teacher_id")

    exam_doc = {
        **exam_data.model_dump(),
        "teacher_id": teacher_id,
        # denormalize for student access + UI
        "class_name": class_info.get("name") if class_info else "",
        "grade": class_info.get("grade") if class_info else "",
        # ensure timezone-aware datetimes are persisted consistently
        "start_time": _to_utc(exam_data.start_time),
        "end_time": _to_utc(exam_data.end_time),
        "secret_key": secret_key,
        "submission_count": "0",
        "score_total": "0",
        "highest_score": "0",
        "violation_total": "0",
    }

    exam_id = await persistence.exams.insert_one(exam_doc)
    return ExamCreateResponse(
        id=exam_id, secret_key=secret_key, message="Exam created successfully"
    )


@router.get("", response_model=List[dict])
async def get_exams(
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> List[dict]:
    """Get exams filtered by role (admin: all, teacher: created, student: class exams)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    if role == "admin":
        exams = await persistence.exams.list_all()
        return [exam_response_helper(e) for e in exams]

    if role == "student":
        user = await persistence.users.get_by_id(user_id)
        if not user:
            return []
        user_class_name = user.get("class_name")
        user_grade = user.get("grade")
        if not user_class_name or not user_grade:
            return []

        # Get class_id via lookup
        cls = await persistence.classes.get_by_name_grade(
            user_class_name, int(user_grade)
        )
        if not cls:
            return []

        # Fetch exams for class + all student submissions in parallel
        class_id = cls.get("class_id")
        exams_task = persistence.exams.list_by_class(class_id)
        submissions_task = persistence.submissions.list_by_student(user_id)

        class_exams, student_submissions = await asyncio.gather(
            exams_task, submissions_task
        )

        # Build submission lookup by exam_id
        submission_by_exam = {sub.get("exam_id"): sub for sub in student_submissions}

        filtered = []
        for exam in class_exams:
            exam_id = exam.get("exam_id")
            exam_dict = exam_response_helper(exam)
            submission = submission_by_exam.get(exam_id)
            if submission:
                exam_dict["status"] = submission.get("status", "completed")
                exam_dict["submitted_at"] = submission.get("submitted_at")
                exam_dict["violation_count"] = int(submission.get("violation_count", 0))
            else:
                exam_dict["status"] = "pending"
            filtered.append(exam_dict)
        return filtered

    if role == "teacher":
        # Include exams created by the teacher + exams for classes they teach (incl. subject teacher)
        teacher_exams = await persistence.exams.list_by_teacher(user_id)

        # Scan classes once to find subject-teacher assignments (ClassRepo only indexes homeroom).
        all_classes = await persistence.classes.list_all()
        class_ids = []
        for c in all_classes:
            if c.get("homeroom_teacher_id") == user_id:
                class_ids.append(c.get("class_id"))
                continue
            for st in c.get("subject_teachers", []):
                if isinstance(st, dict) and st.get("teacher_id") == user_id:
                    class_ids.append(c.get("class_id"))
                    break

        class_ids = [cid for cid in class_ids if cid]
        class_exam_lists = await asyncio.gather(
            *[persistence.exams.list_by_class(cid) for cid in sorted(set(class_ids))]
        )
        class_exams = [e for sublist in class_exam_lists for e in sublist]

        merged: dict[str, dict] = {}
        for e in teacher_exams + class_exams:
            eid = e.get("exam_id") or e.get("id")
            if eid:
                merged[eid] = e

        return [exam_response_helper(e) for e in merged.values()]

    raise HTTPException(status_code=403, detail="Invalid role")


@router.post("/{exam_id}/verify-key", response_model=ExamVerifyKeyResponse)
async def verify_exam_key(
    exam_id: str,
    body: ExamKeyVerify,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamVerifyKeyResponse:
    """Verify exam secret key (student only)."""
    if str(current_user.get("role", "")) != "student":
        raise HTTPException(
            status_code=403, detail="Only students can verify exam keys"
        )

    persistence = get_persistence(request)
    exam = await persistence.exams.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    stored_key = (exam.get("secret_key") or "").strip().upper()
    provided_key = (body.key or "").strip().upper()

    if not stored_key:
        return ExamVerifyKeyResponse(valid=True)

    if stored_key != provided_key:
        raise HTTPException(
            status_code=400, detail="Invalid exam key. Please check and try again."
        )

    return ExamVerifyKeyResponse(valid=True)


@router.get("/{exam_id}/status", response_model=ExamStatusResponse)
async def get_exam_status(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
):
    """Get exam submission status for current student."""
    persistence = get_persistence(request)
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    submission = await persistence.submissions.get_by_exam_student(exam_id, user_id)

    if not submission:
        return ExamStatusResponse(is_submitted=False)

    return ExamStatusResponse(
        is_submitted=True,
        status=submission.get("status"),
        submitted_at=submission.get("submitted_at"),
        violation_count=int(submission.get("violation_count", 0)),
    )


@router.post("/{exam_id}/submit", response_model=ExamSubmissionResponse)
async def submit_exam(
    exam_id: str,
    submission_data: ExamSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamSubmissionResponse:
    """Submit exam answers (student only)."""
    if str(current_user.get("role", "")) != "student":
        raise HTTPException(status_code=403, detail="Only students can submit exams")

    persistence = get_persistence(request)
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    existing = await persistence.submissions.get_by_exam_student(exam_id, user_id)
    if existing:
        raise HTTPException(status_code=400, detail="Exam already submitted")

    exam = await persistence.exams.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Calculate score
    questions = exam.get("questions", [])
    total_questions = len(questions)
    correct_count = 0
    for i, question in enumerate(questions):
        selected = submission_data.answers.get(str(i))
        if selected is None:
            selected = submission_data.answers.get(i)
        if selected is not None and selected == question.get("correct"):
            correct_count += 1

    score = (correct_count / total_questions) * 10 if total_questions > 0 else 0

    now = datetime.now(timezone.utc)
    submission_doc = {
        "exam_id": exam_id,
        "student_id": user_id,
        "submitted_at": now.isoformat(),
        "score": str(score),
        "correct_count": str(correct_count),
        "total_questions": str(total_questions),
        "status": submission_data.status.value,
        "violation_count": str(submission_data.violation_count),
    }
    await persistence.submissions.insert_one(submission_doc)

    # Delete violations on completed status
    if submission_data.status.value == "completed":
        await persistence.violations.delete_by_exam_student(exam_id, user_id)

    # Update exam counters atomically with optimistic locking
    await persistence.exams.update_counters_safe(exam_id, score)

    return ExamSubmissionResponse(
        exam_id=exam_id,
        student_id=user_id,
        submitted_at=now,
        score=score,
        correct_count=correct_count,
        total_questions=total_questions,
        status=submission_data.status,
        violation_count=submission_data.violation_count,
    )


@router.get("/results/my", response_model=List[ExamResultSummary])
async def get_my_results(
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> List[ExamResultSummary]:
    """Get current student's exam results."""
    if str(current_user.get("role", "")) != "student":
        raise HTTPException(
            status_code=403, detail="Only students can view their results"
        )

    persistence = get_persistence(request)
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    submissions = await persistence.submissions.list_by_student(user_id)
    results = []
    for sub in submissions:
        exam = await persistence.exams.get_by_id(sub.get("exam_id"))
        if not exam:
            continue
        results.append(
            ExamResultSummary(
                exam_id=sub.get("exam_id"),
                exam_title=exam.get("title", ""),
                subject=exam.get("subject", ""),
                score=float(sub.get("score", 0)),
                correct_count=int(sub.get("correct_count", 0)),
                total_questions=int(sub.get("total_questions", 0)),
                status=sub.get("status"),
                submitted_at=sub.get("submitted_at"),
            )
        )
    return results


@router.get("/all-results/summary", response_model=List[ExamResultSummaryList])
async def get_all_results_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> List[ExamResultSummaryList]:
    """Get summary of all exam results (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    if role == "teacher":
        # Include exams created by the teacher + exams for classes they teach (homeroom + subject)
        teacher_exams = await persistence.exams.list_by_teacher(user_id)

        # Get all classes the teacher teaches (homeroom or subject)
        teacher_classes = await persistence.classes.list_by_teacher_any_role(user_id)
        class_ids = [c.get("class_id") for c in teacher_classes if c.get("class_id")]

        class_exam_lists = await asyncio.gather(
            *[persistence.exams.list_by_class(cid) for cid in sorted(set(class_ids))]
        )
        class_exams = [e for sublist in class_exam_lists for e in sublist]

        # Merge and deduplicate
        merged: dict[str, dict] = {}
        for e in teacher_exams + class_exams:
            eid = e.get("exam_id") or e.get("id")
            if eid:
                merged[eid] = e
        exams = list(merged.values())
    else:
        exams = await persistence.exams.list_all()

    summary = []
    for exam in exams:
        exam_id = exam.get("exam_id")
        class_id = exam.get("class_id", "")
        cls = await persistence.classes.get_by_id(class_id)

        # Read counters from denormalized fields
        submission_count = int(exam.get("submission_count", 0))
        score_total = float(exam.get("score_total", 0))
        highest_score = float(exam.get("highest_score", 0))
        violation_total = int(exam.get("violation_total", 0))
        avg_score = score_total / submission_count if submission_count > 0 else 0

        summary.append(
            ExamResultSummaryList(
                id=exam_id or "",
                title=exam.get("title", ""),
                subject=exam.get("subject", ""),
                class_id=class_id,
                class_name=cls.get("name") if cls else "N/A",
                grade=str(cls.get("grade")) if cls else "N/A",
                total_submissions=submission_count,
                average_score=avg_score,
                highest_score=highest_score,
                violations_count=violation_total,
                start_time=exam.get("start_time"),
                end_time=exam.get("end_time"),
            )
        )
    return summary


@router.get("/{exam_id}/submissions", response_model=List[ExamSubmissionSummary])
async def get_exam_submissions(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> List[ExamSubmissionSummary]:
    """Get all submissions for an exam (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    allowed, exam = await can_modify_exam(persistence, role, user_id, exam_id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Permission denied")

    submissions = await persistence.submissions.list_by_exam(exam_id)
    results = []
    for sub in submissions:
        student = await persistence.users.get_by_id(sub.get("student_id"))
        results.append(
            ExamSubmissionSummary(
                student_id=sub.get("student_id"),
                student_name=student.get("name") if student else "Unknown student",
                score=float(sub.get("score", 0)),
                violation_count=int(sub.get("violation_count", 0)),
                status=sub.get("status"),
                submitted_at=sub.get("submitted_at"),
            )
        )
    return results


@router.get("/{exam_id}", response_model=dict)
async def get_exam(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
):
    """Get exam details, with lock status for students."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    allowed, exam = await can_access_exam(persistence, role, user_id, exam_id)
    if not allowed or not exam:
        raise HTTPException(status_code=403, detail="Permission denied")

    if role == "student":
        submission = await persistence.submissions.get_by_exam_student(exam_id, user_id)
        if submission:
            return {
                "id": exam.get("exam_id"),
                "title": exam.get("title"),
                "subject": exam.get("subject"),
                "is_locked": True,
                "submission_status": submission.get("status"),
                "violation_count": submission.get("violation_count", 0),
                "start_time": exam.get("start_time", ""),
                "end_time": exam.get("end_time", ""),
                "lock_reason": (
                    "disqualified"
                    if submission.get("status") == "failed"
                    else "submitted"
                ),
            }

        now = datetime.now(timezone.utc)
        start_time = exam.get("start_time", "")
        end_time = exam.get("end_time", "")

        # Parse start/end times
        if isinstance(start_time, str):
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except Exception:
                start_dt = now
        else:
            start_dt = start_time

        if isinstance(end_time, str):
            try:
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except Exception:
                end_dt = now
        else:
            end_dt = end_time

        if now < start_dt:
            return {
                "id": exam.get("exam_id"),
                "title": exam.get("title"),
                "subject": exam.get("subject"),
                "is_locked": True,
                "lock_reason": "not_started",
                "start_time": start_time,
                "end_time": end_time,
            }
        if now > end_dt:
            return {
                "id": exam.get("exam_id"),
                "title": exam.get("title"),
                "subject": exam.get("subject"),
                "is_locked": True,
                "lock_reason": "expired",
                "start_time": start_time,
                "end_time": end_time,
            }

        # Student can access exam content — add server-authoritative time fields
        seconds_left = max(0, int((end_dt - now).total_seconds()))
        return {
            **exam_response_helper(exam, include_secret=False),
            "is_locked": False,
            "lock_reason": None,
            "server_time": now.isoformat(),
            "seconds_left": seconds_left,
        }

    include_secret = role in ["teacher", "admin"]
    return exam_response_helper(exam, include_secret=include_secret)


@router.patch("/{exam_id}", response_model=ExamUpdateResponse)
async def update_exam(
    exam_id: str,
    exam_data: ExamUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamUpdateResponse:
    """Update exam details (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    allowed, exam = await can_modify_exam(persistence, role, user_id, exam_id)
    if not allowed:
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        raise HTTPException(
            status_code=403, detail="Permission denied to edit this exam"
        )

    update_dict = {k: v for k, v in exam_data.model_dump().items() if v is not None}
    if not update_dict:
        return ExamUpdateResponse(message="No changes provided")

    def _to_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    if "start_time" in update_dict and isinstance(update_dict["start_time"], datetime):
        update_dict["start_time"] = _to_utc(update_dict["start_time"])
    if "end_time" in update_dict and isinstance(update_dict["end_time"], datetime):
        update_dict["end_time"] = _to_utc(update_dict["end_time"])

    await persistence.exams.update(exam_id, update_dict)
    return ExamUpdateResponse(message="Exam updated successfully")


@router.delete("/{exam_id}", response_model=ExamDeleteResponse)
async def delete_exam(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamDeleteResponse:
    """Delete an exam (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    allowed, exam = await can_modify_exam(persistence, role, user_id, exam_id)
    if not allowed:
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        raise HTTPException(
            status_code=403, detail="Permission denied to delete this exam"
        )

    await persistence.exams.delete(exam_id)
    return ExamDeleteResponse(message="Exam deleted successfully")


@router.get("/{exam_id}/secret-key", response_model=ExamSecretKeyResponse)
async def get_exam_secret_key(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamSecretKeyResponse:
    """Get exam secret key (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")
    allowed, exam = await can_modify_exam(persistence, role, user_id, exam_id)
    if not allowed or not exam:
        raise HTTPException(
            status_code=404 if not exam else 403,
            detail="Exam not found" if not exam else "Permission denied",
        )

    return ExamSecretKeyResponse(secret_key=exam.get("secret_key") or "")


@router.post("/{exam_id}/regenerate-key", response_model=ExamRegenerateKeyResponse)
async def regenerate_exam_secret_key(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> ExamRegenerateKeyResponse:
    """Regenerate exam secret key (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")
    allowed, exam = await can_modify_exam(persistence, role, user_id, exam_id)
    if not allowed or not exam:
        raise HTTPException(
            status_code=404 if not exam else 403,
            detail="Exam not found" if not exam else "Permission denied",
        )

    new_key = secrets.token_hex(3).upper()
    await persistence.exams.update(exam_id, {"secret_key": new_key})
    return ExamRegenerateKeyResponse(
        secret_key=new_key, message="Secret key regenerated successfully"
    )


@router.get("/violations/all", response_model=List[ExamViolation])
async def get_all_violations(
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> List[ExamViolation]:
    """Get all exam violations (teacher/admin only)."""
    persistence = get_persistence(request)
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user.get("user_id") or current_user.get("_id") or "")

    # If teacher, filter by their classes
    if role == "teacher":
        teacher_classes = await persistence.classes.list_by_teacher_any_role(user_id)
        class_ids = [c.get("class_id") for c in teacher_classes if c.get("class_id")]

        all_violations = []
        for cid in set(class_ids):
            violations = await persistence.violations.list_by_class(cid)
            all_violations.extend(violations)
    else:
        # Admin sees all - scan violations
        # For now, get from exams
        exams = await persistence.exams.list_all()
        all_violations = []
        for exam in exams:
            violations = await persistence.violations.list_by_exam(exam.get("exam_id"))
            all_violations.extend(violations)

    results = []
    for v in all_violations:
        student = await persistence.users.get_by_id(v.get("student_id"))
        exam = await persistence.exams.get_by_id(v.get("exam_id"))

        results.append(
            ExamViolation(
                id=v.get("exam_id"),
                exam_id=v.get("exam_id"),
                student_id=v.get("student_id") or "",
                student_name=student.get("name") if student else "Unknown student",
                student_class=f"{student.get('grade', '')} {student.get('class_name', '')}".strip()
                or "N/A",
                exam_title=exam.get("title") if exam else "Unknown Exam",
                exam_start=exam.get("start_time") if exam else None,
                exam_end=exam.get("end_time") if exam else None,
                class_id=v.get("class_id") or "unknown",
                subject=v.get("subject", "N/A"),
                violation_type=v.get("type", ""),
                violation_time=v.get("violation_time") or datetime.now(timezone.utc),
                created_at=v.get("created_at"),
                evidence_images=v.get("evidence_images", []) or [],
                metadata=v.get("metadata", {}) or {},
            )
        )
    return results
