import secrets
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
    ExamKeyVerify,
    ExamResponse,
    ExamStatusResponse,
    ExamSubmission,
    ExamUpdate,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


def exam_helper(exam, include_secret: bool = False) -> dict:
    result = {
        "id": str(exam["_id"]),
        "title": exam["title"],
        "description": exam.get("description"),
        "subject": exam["subject"],
        "exam_type": exam.get("exam_type", "15-minute quiz"),
        "teacher_id": exam["teacher_id"],
        "class_id": exam["class_id"],
        "start_time": exam["start_time"],
        "end_time": exam["end_time"],
        "duration": exam.get("duration", 60),
        "has_secret_key": bool(exam.get("secret_key")),
        "questions": exam.get("questions", []),
    }
    if include_secret:
        result["secret_key"] = exam.get("secret_key")
    return result


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
    if new_exam.get("secret_key"):
        new_exam["secret_key"] = str(new_exam["secret_key"]).strip().upper()
    else:
        new_exam["secret_key"] = secrets.token_hex(3).upper()
    result = await exams_collection.insert_one(new_exam)
    return {
        "id": str(result.inserted_id),
        "secret_key": new_exam["secret_key"],
        "message": "Exam created successfully",
    }


@router.get("", response_model=List[dict])
async def get_exams(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    query = {}
    if role == "admin":
        query = {}
    elif role == "student":
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if not u_class or not u_grade:
            return []

        cls = await classes_collection.find_one({"name": u_class, "grade": u_grade})
        if not cls:
            return []

        query = {"class_id": str(cls["_id"])}
    elif role == "teacher":
        teacher_classes = []
        async for cls in classes_collection.find(
            {
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ]
            }
        ):
            teacher_classes.append(str(cls["_id"]))

        query = {
            "$or": [{"teacher_id": user_id}, {"class_id": {"$in": teacher_classes}}]
        }
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    exams = []
    async for exam in exams_collection.find(query):
        e_dict = exam_helper(exam)
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


@router.post("/{exam_id}/verify-key", response_model=dict)
async def verify_exam_key(
    exam_id: str,
    body: ExamKeyVerify,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=403, detail="Only students can verify exam keys"
        )

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    stored_key = (exam.get("secret_key") or "").strip().upper()
    provided_key = (body.key or "").strip().upper()

    if not stored_key:
        return {"valid": True}

    if provided_key != stored_key:
        raise HTTPException(
            status_code=400, detail="Invalid exam key. Please check and try again."
        )

    return {"valid": True}


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

    existing = await submissions_collection.find_one(
        {"exam_id": exam_id, "student_id": str(current_user["_id"])}
    )
    if existing:
        return {"message": "Exam already submitted", "already_submitted": True}

    new_submission = submission_data.model_dump()
    new_submission["exam_id"] = exam_id
    new_submission["student_id"] = str(current_user["_id"])
    new_submission["submitted_at"] = datetime.now(timezone.utc)

    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = exam.get("questions", [])
    total_questions = len(questions)
    correct_count = 0
    student_answers = submission_data.answers or {}
    for i, q in enumerate(questions):
        selected = student_answers.get(str(i))
        if selected is None:
            selected = student_answers.get(i)
        if selected is not None and selected == q.get("correct"):
            correct_count += 1

    score = (correct_count / total_questions) * 10 if total_questions > 0 else 0
    new_submission["score"] = score
    new_submission["correct_count"] = correct_count
    new_submission["total_questions"] = total_questions

    await submissions_collection.insert_one(new_submission)

    if new_submission["status"] == "completed":
        await violations_collection.delete_many(
            {"student_id": str(current_user["_id"]), "exam_id": exam_id}
        )

    return {"message": "Exam submitted successfully"}


@router.get("/results/my", response_model=List[dict])
async def get_my_results(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=403, detail="Only students can view their results"
        )

    student_id = str(current_user["_id"])
    submissions = await submissions_collection.find({"student_id": student_id}).to_list(
        None
    )

    results = []
    for sub in submissions:
        raw_exam_id = str(sub.get("exam_id", "")).strip()
        if not ObjectId.is_valid(raw_exam_id):
            continue
        exam = await exams_collection.find_one({"_id": ObjectId(raw_exam_id)})
        if not exam:
            continue
        results.append(
            {
                "exam_id": raw_exam_id,
                "exam_title": exam["title"],
                "subject": exam["subject"],
                "score": sub.get("score", 0),
                "correct_count": sub.get("correct_count", 0),
                "total_questions": sub.get("total_questions", 0),
                "status": sub.get("status"),
                "submitted_at": sub.get("submitted_at"),
            }
        )

    results.sort(
        key=lambda x: x["submitted_at"] if x["submitted_at"] else datetime.min,
        reverse=True,
    )
    return results


@router.get("/all-results/summary", response_model=List[dict])
async def get_all_results_summary(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = str(current_user["_id"])
    query = {}
    if role == "teacher":
        teacher_classes = []
        async for cls in classes_collection.find(
            {
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ]
            }
        ):
            teacher_classes.append(str(cls["_id"]))

        query = {"class_id": {"$in": teacher_classes}}

    exams = await exams_collection.find(query).to_list(None)
    summary = []
    for exam in exams:
        exam_id = str(exam["_id"])
        class_id = exam.get("class_id")

        class_info = None
        if class_id and ObjectId.is_valid(class_id):
            class_info = await classes_collection.find_one({"_id": ObjectId(class_id)})

        pipeline = [
            {"$match": {"exam_id": exam_id}},
            {
                "$group": {
                    "_id": "$exam_id",
                    "total_submissions": {"$sum": 1},
                    "average_score": {"$avg": "$score"},
                    "highest_score": {"$max": "$score"},
                    "violations_sum": {"$sum": "$violation_count"},
                }
            },
        ]
        stats_list = await submissions_collection.aggregate(pipeline).to_list(length=1)
        stats = (
            stats_list[0]
            if stats_list
            else {
                "total_submissions": 0,
                "average_score": 0,
                "highest_score": 0,
                "violations_sum": 0,
            }
        )
        summary.append(
            {
                "id": exam_id,
                "title": exam["title"],
                "subject": exam["subject"],
                "class_id": class_id,
                "class_name": class_info.get("name") if class_info else "N/A",
                "grade": class_info.get("grade") if class_info else "N/A",
                "total_submissions": stats["total_submissions"],
                "average_score": stats["average_score"] or 0,
                "highest_score": stats["highest_score"] or 0,
                "violations_count": stats["violations_sum"] or 0,
            }
        )
    return summary


@router.get("/{exam_id}/submissions", response_model=List[dict])
async def get_exam_submissions(
    exam_id: str, current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    if role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    user_id = str(current_user["_id"])
    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if role == "teacher":
        class_id = exam.get("class_id")
        # Check if teacher is assigned to this class or created the exam
        cls = await classes_collection.find_one(
            {
                "_id": ObjectId(class_id),
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ],
            }
        )
        if not cls and exam.get("teacher_id") != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")

    submissions = await submissions_collection.find({"exam_id": exam_id}).to_list(None)

    results = []
    for sub in submissions:
        student_id = sub.get("student_id")
        student = None
        if student_id and ObjectId.is_valid(student_id):
            student = await users_collection.find_one({"_id": ObjectId(student_id)})

        results.append(
            {
                "student_id": student_id,
                "student_name": student.get("name") if student else "Unknown student",
                "score": sub.get("score", 0),
                "violation_count": sub.get("violation_count", 0),
                "status": sub.get("status"),
                "submitted_at": sub.get("submitted_at"),
            }
        )

    return results


@router.get("/{exam_id}", response_model=dict)
async def get_exam(exam_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")
    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    role = current_user.get("role")
    user_id = str(current_user["_id"])

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
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if u_class and u_grade:
            cls = await classes_collection.find_one(
                {"_id": ObjectId(exam["class_id"]), "name": u_class, "grade": u_grade}
            )
            if cls:
                has_permission = True
    elif role == "teacher":
        if exam["teacher_id"] == user_id:
            has_permission = True
        else:
            cls = await classes_collection.find_one(
                {
                    "_id": ObjectId(exam["class_id"]),
                    "$or": [
                        {"homeroom_teacher_id": user_id},
                        {"subject_teachers.teacher_id": user_id},
                    ],
                }
            )
            if cls:
                has_permission = True

    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied")

    include_secret = role in ["teacher", "admin"]
    return exam_helper(exam, include_secret=include_secret)


@router.patch("/{exam_id}", response_model=dict)
async def update_exam(
    exam_id: str, exam_data: ExamUpdate, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")

    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

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
                {
                    "_id": ObjectId(exam["class_id"]),
                    "$or": [
                        {"homeroom_teacher_id": user_id},
                        {"subject_teachers.teacher_id": user_id},
                    ],
                }
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
                {
                    "_id": ObjectId(exam["class_id"]),
                    "$or": [
                        {"homeroom_teacher_id": user_id},
                        {"subject_teachers.teacher_id": user_id},
                    ],
                }
            )
            if cls:
                has_permission = True

    if not has_permission:
        raise HTTPException(
            status_code=403, detail="Permission denied to delete this exam"
        )

    await exams_collection.delete_one({"_id": ObjectId(exam_id)})
    return {"message": "Exam deleted successfully"}


@router.get("/{exam_id}/secret-key", response_model=dict)
async def get_exam_secret_key(
    exam_id: str, current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")
    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    user_id = str(current_user["_id"])
    if role == "teacher" and exam["teacher_id"] != user_id:
        cls = await classes_collection.find_one(
            {
                "_id": ObjectId(exam["class_id"]),
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ],
            }
        )
        if not cls:
            raise HTTPException(status_code=403, detail="Permission denied")

    return {"secret_key": exam.get("secret_key")}


@router.post("/{exam_id}/regenerate-key", response_model=dict)
async def regenerate_exam_secret_key(
    exam_id: str, current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not ObjectId.is_valid(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID")
    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    user_id = str(current_user["_id"])
    if role == "teacher" and exam["teacher_id"] != user_id:
        cls = await classes_collection.find_one(
            {
                "_id": ObjectId(exam["class_id"]),
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ],
            }
        )
        if not cls:
            raise HTTPException(status_code=403, detail="Permission denied")

    new_key = secrets.token_hex(3).upper()
    await exams_collection.update_one(
        {"_id": ObjectId(exam_id)}, {"$set": {"secret_key": new_key}}
    )
    return {"secret_key": new_key, "message": "Secret key regenerated successfully"}


@router.get("/violations/all", response_model=List[dict])
async def get_all_violations(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    user_id = str(current_user["_id"])

    query = {}
    if role == "teacher":
        teacher_classes = []
        async for cls in classes_collection.find(
            {
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ]
            }
        ):
            teacher_classes.append(str(cls["_id"]))
        query = {"class_id": {"$in": teacher_classes}}

    violations = []
    async for v in violations_collection.find(query).sort("violation_time", -1):
        student = await users_collection.find_one({"_id": ObjectId(v["student_id"])})

        if v.get("class_id") == "unknown" and student:
            current_class_id = student.get("class_id")
            if not current_class_id:
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
