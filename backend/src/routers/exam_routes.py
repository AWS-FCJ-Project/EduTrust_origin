from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_, select, update, delete
from src.auth.dependencies import get_current_user
from src.deps import get_db_session
from src.models import Class, ClassSubjectTeacher, Exam, Submission, User, Violation
from src.schemas.school_schemas import (
    ExamCreate,
    ExamKeyVerify,
    ExamStatusResponse,
    ExamSubmission,
    ExamUpdate,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


def exam_helper(exam: dict, include_secret: bool = False) -> dict:
    """Backward-compatible helper for tests and legacy dict-shaped exam objects."""
    exam_type = exam.get("exam_type") or "15-minute quiz"
    result = {
        "id": str(exam.get("_id") or exam.get("id") or ""),
        "title": exam.get("title"),
        "description": exam.get("description"),
        "subject": exam.get("subject"),
        "exam_type": exam_type,
        "teacher_id": exam.get("teacher_id"),
        "class_id": exam.get("class_id"),
        "start_time": exam.get("start_time"),
        "end_time": exam.get("end_time"),
        "duration": exam.get("duration", 60),
        "has_secret_key": bool(exam.get("secret_key")),
        "questions": exam.get("questions", []),
    }
    if include_secret:
        result["secret_key"] = exam.get("secret_key")
    return result


def _exam_to_dict(exam: Exam, *, include_secret: bool = False) -> dict:
    result = {
        "id": str(exam.id),
        "title": exam.title,
        "description": exam.description,
        "subject": exam.subject,
        "exam_type": exam.exam_type,
        "teacher_id": exam.teacher_id,
        "class_id": exam.class_id,
        "start_time": exam.start_time,
        "end_time": exam.end_time,
        "duration": exam.duration,
        "has_secret_key": bool(exam.secret_key),
        "questions": list(exam.questions or []),
    }
    if include_secret:
        result["secret_key"] = exam.secret_key
    return result


async def _teacher_class_ids(session, *, teacher_id: str) -> list[str]:
    classes_res = await session.execute(
        select(Class.id)
        .distinct()
        .outerjoin(ClassSubjectTeacher, ClassSubjectTeacher.class_id == Class.id)
        .where(
            (Class.homeroom_teacher_id == teacher_id)
            | (ClassSubjectTeacher.teacher_id == teacher_id)
        )
    )
    return [str(row[0]) for row in classes_res.all() if row and row[0]]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_data: ExamCreate,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Only teachers or admins can create exams")

    user_id = str(current_user["_id"])
    class_id = str(exam_data.class_id)

    cls_res = await session.execute(select(Class).where(Class.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if class_id not in teacher_classes:
            raise HTTPException(status_code=403, detail="You do not teach this class")

    new_exam = exam_data.model_dump()
    secret_key = (new_exam.get("secret_key") or "").strip().upper() or secrets.token_hex(3).upper()

    exam = Exam(
        title=new_exam["title"],
        description=new_exam.get("description"),
        subject=new_exam["subject"],
        exam_type=new_exam.get("exam_type") or "15-minute quiz",
        teacher_id=user_id,
        class_id=class_id,
        start_time=new_exam["start_time"],
        end_time=new_exam["end_time"],
        duration=int(new_exam.get("duration") or 60),
        secret_key=secret_key,
        questions=new_exam.get("questions") or [],
    )
    session.add(exam)
    await session.flush()
    return {"id": str(exam.id), "secret_key": secret_key, "message": "Exam created successfully"}


@router.get("", response_model=List[dict])
async def get_exams(current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    exams: list[Exam] = []

    if role == "admin":
        result = await session.execute(select(Exam))
        exams = result.scalars().all()
    elif role == "student":
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if not u_class or not u_grade:
            return []
        cls_res = await session.execute(select(Class).where(Class.name == u_class, Class.grade == int(u_grade)))
        cls = cls_res.scalar_one_or_none()
        if not cls:
            return []
        result = await session.execute(select(Exam).where(Exam.class_id == cls.id))
        exams = result.scalars().all()
    elif role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        result = await session.execute(
            select(Exam).where(or_(Exam.teacher_id == user_id, Exam.class_id.in_(teacher_classes)))
        )
        exams = result.scalars().all()
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    payload: list[dict] = []
    for exam in exams:
        e_dict = _exam_to_dict(exam, include_secret=False)
        if role == "student":
            sub_res = await session.execute(
                select(Submission).where(Submission.exam_id == exam.id, Submission.student_id == user_id)
            )
            submission = sub_res.scalar_one_or_none()
            if submission:
                e_dict["status"] = submission.status
                e_dict["submitted_at"] = submission.submitted_at
                e_dict["violation_count"] = submission.violation_count
            else:
                e_dict["status"] = "pending"
        payload.append(e_dict)
    return payload


@router.post("/{exam_id}/verify-key", response_model=dict)
async def verify_exam_key(
    exam_id: str,
    body: ExamKeyVerify,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can verify exam key")

    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    stored_key = (exam.secret_key or "").strip().upper()
    provided_key = (body.key or "").strip().upper()
    if not stored_key:
        return {"valid": True}
    if provided_key != stored_key:
        raise HTTPException(status_code=400, detail="Invalid exam key. Please check and try again.")
    return {"valid": True}


@router.get("/{exam_id}/status", response_model=ExamStatusResponse)
async def get_exam_status(
    exam_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    submission_res = await session.execute(
        select(Submission).where(
            Submission.exam_id == exam_id,
            Submission.student_id == str(current_user["_id"]),
        )
    )
    submission = submission_res.scalar_one_or_none()
    if not submission:
        return {"is_submitted": False}
    return {
        "is_submitted": True,
        "status": submission.status,
        "submitted_at": submission.submitted_at,
        "violation_count": submission.violation_count,
    }


@router.post("/{exam_id}/submit", response_model=dict)
async def submit_exam(
    exam_id: str,
    submission_data: ExamSubmission,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can submit exams")

    student_id = str(current_user["_id"])
    existing_res = await session.execute(
        select(Submission).where(Submission.exam_id == exam_id, Submission.student_id == student_id)
    )
    existing = existing_res.scalar_one_or_none()
    if existing:
        return {"message": "Exam already submitted", "already_submitted": True}

    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = list(exam.questions or [])
    total_questions = len(questions)
    correct_count = 0
    student_answers = submission_data.answers or {}

    for i, q in enumerate(questions):
        selected = student_answers.get(str(i))
        if selected is None:
            selected = student_answers.get(i)
        if selected is not None and selected == (q.get("correct")):
            correct_count += 1

    score = (correct_count / total_questions) * 10 if total_questions > 0 else 0.0

    new_submission = Submission(
        exam_id=exam_id,
        student_id=student_id,
        answers=submission_data.answers or {},
        violation_count=int(submission_data.violation_count or 0),
        status=submission_data.status or "completed",
        submitted_at=datetime.now(timezone.utc),
        score=float(score),
        correct_count=int(correct_count),
        total_questions=int(total_questions),
    )
    session.add(new_submission)

    if new_submission.status == "completed":
        await session.execute(
            delete(Violation).where(Violation.student_id == student_id, Violation.exam_id == exam_id)
        )

    return {"message": "Exam submitted successfully"}


@router.get("/results/my", response_model=List[dict])
async def get_my_results(current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can view their results")

    student_id = str(current_user["_id"])
    result = await session.execute(
        select(Submission, Exam)
        .join(Exam, Exam.id == Submission.exam_id)
        .where(Submission.student_id == student_id)
        .order_by(Submission.submitted_at.desc())
    )
    rows = result.all()
    payload: list[dict] = []
    for sub, exam in rows:
        payload.append(
            {
                "exam_id": str(exam.id),
                "exam_title": exam.title,
                "subject": exam.subject,
                "score": float(sub.score or 0),
                "correct_count": int(sub.correct_count or 0),
                "total_questions": int(sub.total_questions or 0),
                "status": sub.status,
                "submitted_at": sub.submitted_at,
            }
        )
    return payload


@router.get("/all-results/summary", response_model=List[dict])
async def get_all_results_summary(current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user["_id"])

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        exams_res = await session.execute(
            select(Exam).where(or_(Exam.class_id.in_(teacher_classes), Exam.teacher_id == user_id))
        )
    else:
        exams_res = await session.execute(select(Exam))

    exams = exams_res.scalars().all()
    if not exams:
        return []

    exam_ids = [e.id for e in exams]

    # Load class info
    class_ids = {e.class_id for e in exams if e.class_id}
    classes_by_id: dict[str, Class] = {}
    if class_ids:
        cls_res = await session.execute(select(Class).where(Class.id.in_(list(class_ids))))
        for c in cls_res.scalars().all():
            classes_by_id[str(c.id)] = c

    stats_res = await session.execute(
        select(
            Submission.exam_id,
            func.count(Submission.id),
            func.avg(Submission.score),
            func.max(Submission.score),
            func.sum(Submission.violation_count),
        )
        .where(Submission.exam_id.in_(exam_ids))
        .group_by(Submission.exam_id)
    )
    stats_map = {
        row[0]: {
            "total_submissions": int(row[1] or 0),
            "average_score": float(row[2] or 0),
            "highest_score": float(row[3] or 0),
            "violations_sum": int(row[4] or 0),
        }
        for row in stats_res.all()
    }

    summary: list[dict] = []
    for exam in exams:
        class_info = classes_by_id.get(str(exam.class_id))
        stats = stats_map.get(
            exam.id,
            {"total_submissions": 0, "average_score": 0, "highest_score": 0, "violations_sum": 0},
        )
        summary.append(
            {
                "id": str(exam.id),
                "title": exam.title,
                "subject": exam.subject,
                "class_id": exam.class_id,
                "class_name": class_info.name if class_info else "N/A",
                "grade": class_info.grade if class_info else "N/A",
                "total_submissions": stats["total_submissions"],
                "average_score": stats["average_score"],
                "highest_score": stats["highest_score"],
                "violations_count": stats["violations_sum"],
                "start_time": exam.start_time,
                "end_time": exam.end_time,
            }
        )
    return summary


@router.get("/{exam_id}/submissions", response_model=List[dict])
async def get_exam_submissions(exam_id: str, current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user["_id"])
    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if (exam.class_id not in teacher_classes) and (exam.teacher_id != user_id):
            raise HTTPException(status_code=403, detail="Permission denied")

    subs_res = await session.execute(select(Submission).where(Submission.exam_id == exam_id))
    subs = subs_res.scalars().all()
    if not subs:
        return []

    student_ids = {s.student_id for s in subs if s.student_id}
    students_by_id: dict[str, User] = {}
    if student_ids:
        st_res = await session.execute(select(User).where(User.id.in_(list(student_ids))))
        for s in st_res.scalars().all():
            students_by_id[str(s.id)] = s

    results: list[dict] = []
    for sub in subs:
        student = students_by_id.get(str(sub.student_id))
        results.append(
            {
                "student_id": sub.student_id,
                "student_name": student.name if student else "Unknown student",
                "score": float(sub.score or 0),
                "violation_count": int(sub.violation_count or 0),
                "status": sub.status,
                "submitted_at": sub.submitted_at,
            }
        )
    return results


@router.get("/{exam_id}", response_model=dict)
async def get_exam(exam_id: str, current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    role = current_user.get("role")
    user_id = str(current_user["_id"])
    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if (exam.class_id not in teacher_classes) and (exam.teacher_id != user_id):
            raise HTTPException(status_code=403, detail="Permission denied")

    return _exam_to_dict(exam, include_secret=False)


@router.patch("/{exam_id}", response_model=dict)
async def update_exam(
    exam_id: str,
    exam_data: ExamUpdate,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user["_id"])
    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if (exam.class_id not in teacher_classes) and (exam.teacher_id != user_id):
            raise HTTPException(status_code=403, detail="Permission denied")

    update_dict = {
        k: v
        for k, v in exam_data.model_dump().items()
        if v is not None and str(v).strip() != "" and str(v).lower() != "string"
    }
    if "secret_key" in update_dict and update_dict["secret_key"]:
        update_dict["secret_key"] = str(update_dict["secret_key"]).strip().upper()
    if not update_dict:
        return {"message": "No changes provided"}

    await session.execute(update(Exam).where(Exam.id == exam_id).values(**update_dict))
    return {"message": "Exam updated successfully"}


@router.delete("/{exam_id}", response_model=dict)
async def delete_exam(exam_id: str, current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user["_id"])
    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if (exam.class_id not in teacher_classes) and (exam.teacher_id != user_id):
            raise HTTPException(status_code=403, detail="Permission denied")

    await session.execute(delete(Submission).where(Submission.exam_id == exam_id))
    await session.execute(delete(Violation).where(Violation.exam_id == exam_id))
    await session.execute(delete(Exam).where(Exam.id == exam_id))
    return {"message": "Exam deleted successfully"}


@router.get("/{exam_id}/secret-key", response_model=dict)
async def get_exam_secret_key(exam_id: str, current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user["_id"])
    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if (exam.class_id not in teacher_classes) and (exam.teacher_id != user_id):
            raise HTTPException(status_code=403, detail="Permission denied")

    return {"secret_key": exam.secret_key}


@router.post("/{exam_id}/regenerate-key", response_model=dict)
async def regenerate_exam_secret_key(exam_id: str, current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user["_id"])
    exam_res = await session.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        if (exam.class_id not in teacher_classes) and (exam.teacher_id != user_id):
            raise HTTPException(status_code=403, detail="Permission denied")

    new_key = secrets.token_hex(3).upper()
    await session.execute(update(Exam).where(Exam.id == exam_id).values(secret_key=new_key))
    return {"secret_key": new_key, "message": "Secret key regenerated successfully"}


@router.get("/violations/all", response_model=List[dict])
async def get_all_violations(current_user: dict = Depends(get_current_user), session=Depends(get_db_session)):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user["_id"])

    violation_query = select(Violation)
    if role == "teacher":
        teacher_classes = await _teacher_class_ids(session, teacher_id=user_id)
        violation_query = violation_query.where(Violation.class_id.in_(teacher_classes))

    violations_res = await session.execute(violation_query)
    violations = violations_res.scalars().all()
    if not violations:
        return []

    student_ids = {v.student_id for v in violations if v.student_id}
    exam_ids = {v.exam_id for v in violations if v.exam_id}

    students_by_id: dict[str, User] = {}
    if student_ids:
        st_res = await session.execute(select(User).where(User.id.in_(list(student_ids))))
        for s in st_res.scalars().all():
            students_by_id[str(s.id)] = s

    exams_by_id: dict[str, Exam] = {}
    if exam_ids:
        ex_res = await session.execute(select(Exam).where(Exam.id.in_(list(exam_ids))))
        for e in ex_res.scalars().all():
            exams_by_id[str(e.id)] = e

    payload: list[dict] = []
    for v in violations:
        student = students_by_id.get(str(v.student_id))
        exam = exams_by_id.get(str(v.exam_id))
        payload.append(
            {
                "id": str(v.id),
                "exam_id": v.exam_id,
                "student_id": v.student_id,
                "class_id": v.class_id,
                "subject": v.subject,
                "type": v.type,
                "timestamp": v.timestamp,
                "violation_time": v.violation_time,
                "evidence_images": list(v.evidence_images or []),
                "metadata": dict(v.metadata_ or {}),
                "student_name": student.name if student else "Unknown student",
                "student_class": f"{student.grade or ''} {student.class_name or ''}".strip()
                if student
                else "N/A",
                "exam_title": exam.title if exam else "Unknown Exam",
                "exam_start": exam.start_time if exam else None,
                "exam_end": exam.end_time if exam else None,
            }
        )

    payload.sort(key=lambda x: x.get("violation_time") or "", reverse=True)
    return payload
