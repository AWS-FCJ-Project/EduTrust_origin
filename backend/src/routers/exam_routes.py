from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from src.auth.dependencies import get_current_user
from src.database import (
    classes_collection,
    exams_collection,
    submissions_collection,
    users_collection,
    violations_collection,
)
from src.schemas.school_schemas import (
    ExamCreate,
    ExamResponse,
    ExamStatusResponse,
    ExamSubmission,
    ExamUpdate,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


def exam_helper(exam) -> dict:
    return {
        "id": str(exam["_id"]),
        "title": exam["title"],
        "description": exam.get("description"),
        "subject": exam["subject"],
        "teacher_id": exam["teacher_id"],
        "class_id": exam["class_id"],
        "start_time": exam["start_time"],
        "end_time": exam["end_time"],
        "duration": exam.get("duration", 60),
        "questions": exam.get("questions", []),
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_data: ExamCreate, current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=403, detail="Only teachers or admins can create exams"
        )

    user_id = str(current_user["_id"])

    # Verify teacher belongs to the class
    class_id = exam_data.class_id
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    cls = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    if role == "teacher":
        is_homeroom = cls.get("homeroom_teacher_id") == user_id
        is_subject = any(
            t.get("teacher_id") == user_id for t in cls.get("subject_teachers", [])
        )
        if not (is_homeroom or is_subject):
            raise HTTPException(status_code=403, detail="You do not teach this class")

    new_exam = exam_data.model_dump()
    new_exam["teacher_id"] = user_id
    result = await exams_collection.insert_one(new_exam)
    return {"id": str(result.inserted_id), "message": "Exam created successfully"}


@router.get("", response_model=List[dict])
async def get_exams(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    query = {}
    if role == "admin":
        query = {}
    elif role == "student":
        # Find class matching student profile
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if not u_class or not u_grade:
            return []

        cls = await classes_collection.find_one({"name": u_class, "grade": u_grade})
        if not cls:
            return []

        query = {"class_id": str(cls["_id"])}
    elif role == "teacher":
        # Teacher sees:
        # 1. Exams they created
        # 2. All exams for classes where they are homeroom teacher

        # Find classes where they are homeroom teacher
        homeroom_classes = []
        async for cls in classes_collection.find({"homeroom_teacher_id": user_id}):
            homeroom_classes.append(str(cls["_id"]))

        query = {
            "$or": [{"teacher_id": user_id}, {"class_id": {"$in": homeroom_classes}}]
        }
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    exams = []
    async for exam in exams_collection.find(query):
        e_dict = exam_helper(exam)
        # For students, attach their specific submission status
        if role == "student":
            submission = await submissions_collection.find_one(
                {"exam_id": e_dict["id"], "student_id": user_id}
            )
            if submission:
                e_dict["status"] = submission.get("status")
                e_dict["submitted_at"] = submission.get("submitted_at")
                e_dict["violation_count"] = submission.get("violation_count", 0)
            else:
                e_dict["status"] = "pending"
        exams.append(e_dict)
    return exams


@router.get("/{exam_id}/status", response_model=ExamStatusResponse)
async def get_exam_status(exam_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    submission = await submissions_collection.find_one(
        {"exam_id": exam_id, "student_id": str(current_user["_id"])}
    )

    if not submission:
        return {"is_submitted": False}

    return {
        "is_submitted": True,
        "status": submission.get("status"),
        "submitted_at": submission.get("submitted_at"),
        "violation_count": submission.get("violation_count", 0),
    }


@router.post("/{exam_id}/submit", response_model=dict)
async def submit_exam(
    exam_id: str,
    submission_data: ExamSubmission,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can submit exams")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    # Check if already submitted
    existing = await submissions_collection.find_one(
        {"exam_id": exam_id, "student_id": str(current_user["_id"])}
    )
    if existing:
        return {"message": "Exam already submitted", "already_submitted": True}

    new_submission = submission_data.model_dump()
    new_submission["exam_id"] = exam_id
    new_submission["student_id"] = str(current_user["_id"])
    new_submission["submitted_at"] = datetime.now(timezone.utc)

    await submissions_collection.insert_one(new_submission)

    if new_submission["status"] == "completed":
        await violations_collection.delete_many(
            {"student_id": str(current_user["_id"]), "exam_id": exam_id}
        )

    return {"message": "Exam submitted successfully"}


@router.get("/{exam_id}", response_model=dict)
async def get_exam(exam_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")
    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Permission check
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    # Check if student already submitted or violated
    now = datetime.now(timezone.utc)
    if role == "student":
        submission = await submissions_collection.find_one(
            {"exam_id": exam_id, "student_id": user_id}
        )
        if submission:
            return {
                "id": str(exam["_id"]),
                "title": exam["title"],
                "subject": exam["subject"],
                "is_locked": True,
                "submission_status": submission.get("status"),
                "violation_count": submission.get("violation_count", 0),
                "lock_reason": (
                    "disqualified"
                    if submission.get("status") == "failed"
                    else "submitted"
                ),
            }

        # Time-based locking for students
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

    has_permission = False
    if role == "admin":
        has_permission = True
    elif role == "student":
        # Student must be in the class defined by their name and grade
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if u_class and u_grade:
            cls = await classes_collection.find_one(
                {"_id": ObjectId(exam["class_id"]), "name": u_class, "grade": u_grade}
            )
            if cls:
                has_permission = True
    elif role == "teacher":
        # Teacher is creator OR homeroom teacher of the class
        if exam["teacher_id"] == user_id:
            has_permission = True
        else:
            cls = await classes_collection.find_one(
                {"_id": ObjectId(exam["class_id"]), "homeroom_teacher_id": user_id}
            )
            if cls:
                has_permission = True

    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied")

    return exam_helper(exam)


@router.patch("/{exam_id}", response_model=dict)
async def update_exam(
    exam_id: str, exam_data: ExamUpdate, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Permission check
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    has_permission = False
    if role == "admin":
        has_permission = True
    elif role == "teacher":
        if exam["teacher_id"] == user_id:
            has_permission = True
        else:
            cls = await classes_collection.find_one(
                {"_id": ObjectId(exam["class_id"]), "homeroom_teacher_id": user_id}
            )
            if cls:
                has_permission = True

    if not has_permission:
        raise HTTPException(
            status_code=403, detail="Permission denied to edit this exam"
        )

    update_dict = {k: v for k, v in exam_data.model_dump().items() if v is not None}
    if not update_dict:
        return {"message": "No changes provided"}

    await exams_collection.update_one({"_id": ObjectId(exam_id)}, {"$set": update_dict})
    return {"message": "Exam updated successfully"}


@router.delete("/{exam_id}", response_model=dict)
async def delete_exam(exam_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Permission check
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    has_permission = False
    if role == "admin":
        has_permission = True
    elif role == "teacher":
        if exam["teacher_id"] == user_id:
            has_permission = True
        else:
            cls = await classes_collection.find_one(
                {"_id": ObjectId(exam["class_id"]), "homeroom_teacher_id": user_id}
            )
            if cls:
                has_permission = True

    if not has_permission:
        raise HTTPException(
            status_code=403, detail="Permission denied to delete this exam"
        )

    await exams_collection.delete_one({"_id": ObjectId(exam_id)})
    return {"message": "Exam deleted successfully"}


@router.get("/violations/all", response_model=List[dict])
async def get_all_violations(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user["_id"])

    # Teachers see violations from classes they manage
    query = {}
    if role == "teacher":
        homeroom_classes = []
        async for cls in classes_collection.find({"homeroom_teacher_id": user_id}):
            homeroom_classes.append(str(cls["_id"]))
        query = {"class_id": {"$in": homeroom_classes}}

    violations = []
    async for v in violations_collection.find(query).sort("violation_time", -1):
        # Attach student info
        student = await users_collection.find_one({"_id": ObjectId(v["student_id"])})

        # Self-healing: if class_id is unknown, try to fix it
        if v.get("class_id") == "unknown" and student:
            current_class_id = student.get("class_id")
            if not current_class_id:
                # Try fallback matching by name/grade
                class_info = await classes_collection.find_one(
                    {"name": student.get("class_name"), "grade": student.get("grade")}
                )
                if class_info:
                    current_class_id = str(class_info["_id"])

            if current_class_id:
                await violations_collection.update_one(
                    {"_id": v["_id"]}, {"$set": {"class_id": str(current_class_id)}}
                )
                v["class_id"] = str(current_class_id)

        if student:
            v["student_name"] = student.get("name", "Unknown student")
            grade = str(student.get("grade", ""))
            class_name = student.get("class_name", "")
            v["student_class"] = f"{grade} {class_name}".strip()
        else:
            v["student_name"] = "Unknown student"
            v["student_class"] = "N/A"

        # Attach exam info (Times and Full Title)
        # Robust lookup by ObjectId or String
        exam = None
        raw_exam_id = str(v.get("exam_id", "")).strip()
        try:
            exam = await exams_collection.find_one({"_id": ObjectId(raw_exam_id)})
        except:
            exam = await exams_collection.find_one({"_id": raw_exam_id})

        if exam:
            v["exam_title"] = exam.get("title", "Unknown Exam")
            v["exam_start"] = exam.get("start_time")
            v["exam_end"] = exam.get("end_time")
            # Update subject if it was N/A
            if v.get("subject") == "N/A":
                v["subject"] = exam.get("subject", "N/A")
                await violations_collection.update_one(
                    {"_id": v["_id"]}, {"$set": {"subject": v["subject"]}}
                )
        else:
            v["exam_title"] = "Unknown Exam"

        v["id"] = str(v["_id"])
        del v["_id"]
        violations.append(v)

    return violations
