from datetime import datetime, timezone
from typing import Annotated, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.dependencies import get_current_user
from src.database.exam_handler import ExamHandler
from src.schemas.school_schemas import (
    ExamCreate,
    ExamKeyVerify,
    ExamSubmission,
    ExamUpdate,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


def get_exam_handler(request: Request) -> ExamHandler:
    return request.app.state.exam_handler


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_exam(
    exam_data: ExamCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=403, detail="Only teachers or admins can create exams"
        )

    if not ObjectId.is_valid(exam_data.class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    allowed, class_info = handler.can_create_exam(
        role, str(current_user["_id"]), exam_data.class_id
    )
    if not allowed:
        if not class_info:
            raise HTTPException(status_code=404, detail="Class not found")
        raise HTTPException(status_code=403, detail="You do not teach this class")

    result = handler.create_exam(exam_data.model_dump(), str(current_user["_id"]))
    return {
        "id": result["id"],
        "secret_key": result["secret_key"],
        "message": "Exam created successfully",
    }


@router.get("", response_model=List[dict])
def get_exams(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    user_id = str(current_user["_id"])

    if role == "admin":
        return handler.get_all_exams()
    elif role == "student":
        user_class = current_user.get("class_name")
        user_grade = current_user.get("grade")
        if not user_class or not user_grade:
            return []
        class_info = handler._get_classes_collection().find_one({"name": user_class, "grade": user_grade})
        if not class_info:
            return []
        return handler.get_exams_for_student(str(class_info["_id"]), user_id)
    elif role == "teacher":
        return handler.get_exams_for_teacher(user_id)
    else:
        raise HTTPException(status_code=403, detail="Invalid role")


@router.post("/{exam_id}/verify-key", response_model=dict)
def verify_exam_key(
    exam_id: str,
    body: ExamKeyVerify,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if str(current_user.get("role", "")) != "student":
        raise HTTPException(
            status_code=403, detail="Only students can verify exam keys"
        )

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    is_valid, exam = handler.verify_key(exam_id, body.key)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if not is_valid:
        raise HTTPException(
            status_code=400, detail="Invalid exam key. Please check and try again."
        )

    return {"valid": True}


@router.get("/{exam_id}/status")
def get_exam_status(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    submission = handler.get_submission(exam_id, str(current_user["_id"]))

    if not submission:
        return {"is_submitted": False}

    return {
        "is_submitted": True,
        "status": submission.get("status"),
        "submitted_at": submission.get("submitted_at"),
        "violation_count": submission.get("violation_count", 0),
    }


@router.post("/{exam_id}/submit", response_model=dict)
def submit_exam(
    exam_id: str,
    submission_data: ExamSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if str(current_user.get("role", "")) != "student":
        raise HTTPException(status_code=403, detail="Only students can submit exams")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    user_id = str(current_user["_id"])
    existing = handler.get_submission(exam_id, user_id)
    if existing:
        return {"message": "Exam already submitted", "already_submitted": True}

    result = handler.submit_exam(
        exam_id,
        user_id,
        submission_data.answers or {},
        submission_data.status or "completed",
    )
    return result


@router.get("/results/my", response_model=List[dict])
def get_my_results(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if str(current_user.get("role", "")) != "student":
        raise HTTPException(
            status_code=403, detail="Only students can view their results"
        )

    return handler.get_student_results(str(current_user["_id"]))


@router.get("/all-results/summary", response_model=List[dict])
def get_all_results_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user["_id"]) if role == "teacher" else None
    return handler.get_all_results_summary(user_id)


@router.get("/{exam_id}/submissions", response_model=List[dict])
def get_exam_submissions(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    allowed, exam = handler.can_access_exam(role, str(current_user["_id"]), exam_id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Permission denied")

    return handler.get_exam_submissions(exam_id)


@router.get("/{exam_id}", response_model=dict)
def get_exam(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    role = str(current_user.get("role", ""))
    user_id = str(current_user["_id"])

    if role == "student":
        allowed, exam = handler.can_access_exam(role, user_id, exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        submission = handler.get_submission(exam_id, user_id)
        if submission:
            return {
                "id": str(exam["_id"]),
                "title": exam["title"],
                "subject": exam["subject"],
                "is_locked": True,
                "submission_status": submission.get("status"),
                "violation_count": submission.get("violation_count", 0),
                "lock_reason": "disqualified" if submission.get("status") == "failed" else "submitted",
            }

        now = datetime.now(timezone.utc)
        if now < exam["start_time"]:
            return {
                "id": str(exam["_id"]),
                "title": exam["title"],
                "subject": exam["subject"],
                "is_locked": True,
                "lock_reason": "not_started",
                "start_time": exam["start_time"],
            }
        if now > exam["end_time"]:
            return {
                "id": str(exam["_id"]),
                "title": exam["title"],
                "subject": exam["subject"],
                "is_locked": True,
                "lock_reason": "expired",
                "end_time": exam["end_time"],
            }

    allowed, exam = handler.can_access_exam(role, user_id, exam_id)
    if not allowed or not exam:
        raise HTTPException(status_code=403, detail="Permission denied")

    include_secret = role in ["teacher", "admin"]
    return handler._format_exam(exam, include_secret=include_secret)


@router.patch("/{exam_id}", response_model=dict)
def update_exam(
    exam_id: str,
    exam_data: ExamUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    role = str(current_user.get("role", ""))
    allowed, exam = handler.can_modify_exam(role, str(current_user["_id"]), exam_id)
    if not allowed:
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        raise HTTPException(status_code=403, detail="Permission denied to edit this exam")

    update_dict = {k: v for k, v in exam_data.model_dump().items() if v is not None}
    if not update_dict:
        return {"message": "No changes provided"}

    handler.update_exam(exam_id, update_dict)
    return {"message": "Exam updated successfully"}


@router.delete("/{exam_id}", response_model=dict)
def delete_exam(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    role = str(current_user.get("role", ""))
    allowed, exam = handler.can_modify_exam(role, str(current_user["_id"]), exam_id)
    if not allowed:
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        raise HTTPException(status_code=403, detail="Permission denied to delete this exam")

    handler.delete_exam(exam_id)
    return {"message": "Exam deleted successfully"}


@router.get("/{exam_id}/secret-key", response_model=dict)
def get_exam_secret_key(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    allowed, exam = handler.can_modify_exam(role, str(current_user["_id"]), exam_id)
    if not allowed or not exam:
        raise HTTPException(
            status_code=404 if not exam else 403,
            detail="Exam not found" if not exam else "Permission denied"
        )

    return {"secret_key": exam.get("secret_key")}


@router.post("/{exam_id}/regenerate-key", response_model=dict)
def regenerate_exam_secret_key(
    exam_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    allowed, exam = handler.can_modify_exam(role, str(current_user["_id"]), exam_id)
    if not allowed or not exam:
        raise HTTPException(
            status_code=404 if not exam else 403,
            detail="Exam not found" if not exam else "Permission denied"
        )

    new_key = handler.regenerate_key(exam_id)
    return {"secret_key": new_key, "message": "Secret key regenerated successfully"}


@router.get("/violations/all", response_model=List[dict])
def get_all_violations(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ExamHandler, Depends(get_exam_handler)],
):
    role = str(current_user.get("role", ""))
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user["_id"]) if role == "teacher" else None
    return handler.get_all_violations(user_id)
