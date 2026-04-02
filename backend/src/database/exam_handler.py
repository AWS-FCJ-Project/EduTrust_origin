import secrets
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo.database import Database
from src.database.db_handler import DBHandler
from src.schemas.exam_schemas import ExamStatus, exam_helper


class ExamHandler(DBHandler):
    """Handler for exam operations using sync pymongo."""

    def __init__(self, database: Database):
        super().__init__(database, "exams")
        self._database = database

    def can_create_exam(
        self, role: str, user_id: str, class_id: str
    ) -> tuple[bool, Optional[dict]]:
        """Check if user can create exam in class. Returns (allowed, class_info)."""
        if role == "admin":
            cls = self._get_classes_collection().find_one({"_id": ObjectId(class_id)})
            return bool(cls), cls

        if role != "teacher":
            return False, None

        cls = self._get_classes_collection().find_one({"_id": ObjectId(class_id)})
        if not cls:
            return False, None

        is_homeroom = cls.get("homeroom_teacher_id") == user_id
        is_subject = any(
            t.get("teacher_id") == user_id for t in cls.get("subject_teachers", [])
        )
        return bool(is_homeroom or is_subject), cls

    def can_access_exam(
        self, role: str, user_id: str, exam_id: str
    ) -> tuple[bool, Optional[dict]]:
        """Check if user can access exam. Returns (allowed, exam)."""
        if role == "admin":
            exam = self.get_exam_by_id(exam_id)
            return True, exam

        exam = self.get_exam_by_id(exam_id)
        if not exam:
            return False, None

        if role == "teacher":
            if exam["teacher_id"] == user_id:
                return True, exam
            cls = self._get_classes_collection().find_one(
                {
                    "_id": ObjectId(exam["class_id"]),
                    "$or": [
                        {"homeroom_teacher_id": user_id},
                        {"subject_teachers.teacher_id": user_id},
                    ],
                }
            )
            return bool(cls), exam

        if role == "student":
            cls = self._get_classes_collection().find_one(
                {"_id": ObjectId(exam["class_id"]), "name": user_id}
            )
            return bool(cls), exam

        return False, exam

    def can_modify_exam(
        self, role: str, user_id: str, exam_id: str
    ) -> tuple[bool, Optional[dict]]:
        """Check if user can modify/delete exam. Returns (allowed, exam)."""
        if role == "admin":
            exam = self.get_exam_by_id(exam_id)
            return True, exam

        exam = self.get_exam_by_id(exam_id)
        if not exam:
            return False, None

        if role != "teacher":
            return False, exam

        if exam["teacher_id"] == user_id:
            return True, exam

        cls = self._get_classes_collection().find_one(
            {
                "_id": ObjectId(exam["class_id"]),
                "$or": [
                    {"homeroom_teacher_id": user_id},
                    {"subject_teachers.teacher_id": user_id},
                ],
            }
        )
        return bool(cls), exam

    def create_exam(self, exam_data: dict, teacher_id: str) -> dict:
        """Create a new exam."""
        new_exam = exam_data.copy()
        new_exam["teacher_id"] = teacher_id
        if new_exam.get("secret_key"):
            new_exam["secret_key"] = str(new_exam["secret_key"]).strip().upper()
        else:
            new_exam["secret_key"] = secrets.token_hex(3).upper()

        result = self.collection.insert_one(new_exam)
        return {
            "id": str(result.inserted_id),
            "secret_key": new_exam["secret_key"],
        }

    def get_exam_by_id(self, exam_id: str) -> Optional[dict]:
        """Get exam by ID."""
        if not ObjectId.is_valid(exam_id):
            return None
        return self.collection.find_one({"_id": ObjectId(exam_id)})

    def get_exams_for_student(self, class_id: str, student_id: str) -> list[dict]:
        """Get exams for a student."""
        exams = []
        for exam_document in self.collection.find({"class_id": class_id}):
            exam_dict = exam_helper(exam_document)
            submission = self._get_submission(
                exam_id=str(exam_document["_id"]), student_id=student_id
            )
            if submission:
                exam_dict["status"] = submission.get("status")
                exam_dict["submitted_at"] = submission.get("submitted_at")
                exam_dict["violation_count"] = submission.get("violation_count", 0)
            else:
                exam_dict["status"] = "pending"
            exams.append(exam_dict)
        return exams

    def get_exams_for_teacher(self, teacher_id: str) -> list[dict]:
        """Get exams created by or assigned to a teacher."""
        exams = []
        for exam_document in self.collection.find({"teacher_id": teacher_id}):
            exams.append(exam_helper(exam_document))
        return exams

    def get_all_exams(self) -> list[dict]:
        """Get all exams for admin."""
        exams = []
        for exam_document in self.collection.find({}):
            exams.append(exam_helper(exam_document))
        return exams

    def verify_key(self, exam_id: str, key: str) -> tuple[bool, Optional[dict]]:
        """Verify exam key. Returns (is_valid, exam)."""
        if not ObjectId.is_valid(exam_id):
            return False, None
        exam_document = self.collection.find_one({"_id": ObjectId(exam_id)})
        if not exam_document:
            return False, None

        stored_key = (exam_document.get("secret_key") or "").strip().upper()
        provided_key = (key or "").strip().upper()

        if not stored_key:
            return True, exam_document

        return stored_key == provided_key, exam_document

    def update_exam(self, exam_id: str, update_data: dict) -> bool:
        """Update an exam."""
        if not ObjectId.is_valid(exam_id):
            return False
        result = self.collection.update_one(
            {"_id": ObjectId(exam_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_exam(self, exam_id: str) -> bool:
        """Delete an exam."""
        if not ObjectId.is_valid(exam_id):
            return False
        result = self.collection.delete_one({"_id": ObjectId(exam_id)})
        return result.deleted_count > 0

    def regenerate_key(self, exam_id: str) -> Optional[str]:
        """Regenerate exam secret key."""
        if not ObjectId.is_valid(exam_id):
            return None
        new_key = secrets.token_hex(3).upper()
        self.collection.update_one(
            {"_id": ObjectId(exam_id)}, {"$set": {"secret_key": new_key}}
        )
        return new_key

    def get_submission(self, exam_id: str, student_id: str) -> Optional[dict]:
        """Get student submission for an exam."""
        return self._get_submission(exam_id, student_id)

    def get_student_results(self, student_id: str) -> list[dict]:
        """Get all exam results for a student."""
        submissions = list(
            self._get_submissions_collection().find({"student_id": student_id})
        )
        results = []
        for submission_document in submissions:
            raw_exam_id = str(submission_document.get("exam_id", "")).strip()
            if not ObjectId.is_valid(raw_exam_id):
                continue
            exam_document = self.collection.find_one({"_id": ObjectId(raw_exam_id)})
            if not exam_document:
                continue
            results.append(
                {
                    "exam_id": raw_exam_id,
                    "exam_title": exam_document["title"],
                    "subject": exam_document["subject"],
                    "score": submission_document.get("score", 0),
                    "correct_count": submission_document.get("correct_count", 0),
                    "total_questions": submission_document.get("total_questions", 0),
                    "status": submission_document.get("status"),
                    "submitted_at": submission_document.get("submitted_at"),
                }
            )
        return results

    def submit_exam(
        self,
        exam_id: str,
        student_id: str,
        answers: dict,
        status_value: ExamStatus = ExamStatus.completed,
    ) -> dict:
        """Submit an exam and calculate score."""
        exam = self.get_exam_by_id(exam_id)
        if not exam:
            return {"error": "Exam not found"}

        questions = exam.get("questions", [])
        total_questions = len(questions)
        correct_count = 0
        for i, question in enumerate(questions):
            selected = answers.get(str(i))
            if selected is None:
                selected = answers.get(i)
            if selected is not None and selected == question.get("correct"):
                correct_count += 1

        score = (correct_count / total_questions) * 10 if total_questions > 0 else 0

        submission = {
            "exam_id": exam_id,
            "student_id": student_id,
            "submitted_at": datetime.now(timezone.utc),
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "status": status_value.value,
        }
        self._get_submissions_collection().insert_one(submission)

        if status_value == ExamStatus.completed:
            self._get_violations_collection().delete_many(
                {"student_id": student_id, "exam_id": exam_id}
            )

        return {
            "exam_id": exam_id,
            "student_id": student_id,
            "submitted_at": submission["submitted_at"],
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "status": status_value.value,
            "violation_count": 0,
        }

    def get_exam_submissions(self, exam_id: str) -> list[dict]:
        """Get all submissions for an exam with student info."""
        submissions = list(
            self._get_submissions_collection().find({"exam_id": exam_id})
        )

        student_object_ids = set()
        for submission in submissions:
            student_id = submission.get("student_id")
            if student_id and ObjectId.is_valid(student_id):
                student_object_ids.add(ObjectId(student_id))

        students_by_id = {}
        if student_object_ids:
            students = self._get_users_collection().find(
                {"_id": {"$in": list(student_object_ids)}}
            )
            students_by_id = {str(s["_id"]): s for s in students}

        results = []
        for submission in submissions:
            student_id = submission.get("student_id")
            student = students_by_id.get(str(student_id))
            results.append(
                {
                    "student_id": student_id,
                    "student_name": (
                        student.get("name") if student else "Unknown student"
                    ),
                    "score": submission.get("score", 0),
                    "violation_count": submission.get("violation_count", 0),
                    "status": submission.get("status"),
                    "submitted_at": submission.get("submitted_at"),
                }
            )
        return results

    def get_all_results_summary(self, teacher_id: Optional[str] = None) -> list[dict]:
        """Get summary of all exam results. If teacher_id provided, filter by teacher's classes."""
        query = {}
        if teacher_id:
            query = {"teacher_id": teacher_id}

        exams = list(self.collection.find(query))

        class_object_ids = set()
        for exam in exams:
            class_id = exam.get("class_id")
            if class_id and ObjectId.is_valid(class_id):
                class_object_ids.add(ObjectId(class_id))

        classes_by_id = {}
        if class_object_ids:
            classes_list = self._get_classes_collection().find(
                {"_id": {"$in": list(class_object_ids)}}
            )
            classes_by_id = {str(c["_id"]): c for c in classes_list}

        summary = []
        for exam in exams:
            exam_id = str(exam["_id"])
            class_id = exam.get("class_id")
            class_info = classes_by_id.get(str(class_id))

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
            stats_list = list(self._get_submissions_collection().aggregate(pipeline))
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
                    "start_time": exam.get("start_time"),
                    "end_time": exam.get("end_time"),
                }
            )
        return summary

    def get_all_violations(self, teacher_id: Optional[str] = None) -> list[dict]:
        """Get all violations, optionally filtered by teacher's classes."""
        query = {}
        if teacher_id:
            # Filter by classes where teacher is homeroom or subject teacher
            teacher_classes = []
            for cls in self._get_classes_collection().find(
                {
                    "$or": [
                        {"homeroom_teacher_id": teacher_id},
                        {"subject_teachers.teacher_id": teacher_id},
                    ]
                }
            ):
                teacher_classes.append(str(cls["_id"]))
            query = {"class_id": {"$in": teacher_classes}}

        violations = []
        for violation in (
            self._get_violations_collection().find(query).sort("violation_time", -1)
        ):
            student = self._get_users_collection().find_one(
                {"_id": ObjectId(str(violation["student_id"]))}
            )

            # Resolve unknown class_id by looking up student's current class
            if violation.get("class_id") == "unknown" and student:
                current_class_id = student.get("class_id")
                if not current_class_id:
                    # Fallback: find class by name and grade
                    class_info = self._get_classes_collection().find_one(
                        {
                            "name": student.get("class_name"),
                            "grade": student.get("grade"),
                        }
                    )
                    if class_info:
                        current_class_id = str(class_info["_id"])

                if current_class_id:
                    # Update violation record with resolved class_id
                    self._get_violations_collection().update_one(
                        {"_id": violation["_id"]},
                        {"$set": {"class_id": str(current_class_id)}},
                    )
                    violation["class_id"] = str(current_class_id)

            # Enrich violation with student info
            if student:
                violation["student_name"] = student.get("name", "Unknown student")
                grade = str(student.get("grade", ""))
                class_name = student.get("class_name", "")
                violation["student_class"] = f"{grade} {class_name}".strip()
            else:
                violation["student_name"] = "Unknown student"
                violation["student_class"] = "N/A"

            # Resolve exam info from exam_id
            exam = None
            raw_exam_id = str(violation.get("exam_id", "")).strip()
            try:
                exam = self.collection.find_one({"_id": ObjectId(raw_exam_id)})
            except:
                exam = self.collection.find_one({"_id": raw_exam_id})

            if exam:
                violation["exam_title"] = exam.get("title", "Unknown Exam")
                violation["exam_start"] = exam.get("start_time")
                violation["exam_end"] = exam.get("end_time")
                # Fill missing subject from exam
                if violation.get("subject") == "N/A":
                    violation["subject"] = exam.get("subject", "N/A")
                    self._get_violations_collection().update_one(
                        {"_id": violation["_id"]},
                        {"$set": {"subject": violation["subject"]}},
                    )
            else:
                violation["exam_title"] = "Unknown Exam"

            # Convert ObjectId to string for response
            violation["id"] = str(violation["_id"])
            del violation["_id"]
            violations.append(violation)

        return violations

    def _get_submission(self, exam_id: str, student_id: str) -> Optional[dict]:
        """Get submission from submissions collection."""
        return self._get_submissions_collection().find_one(
            {"exam_id": exam_id, "student_id": student_id}
        )

    def _get_submissions_collection(self):
        """Get submissions collection."""
        return self._database["submissions"]

    def _get_classes_collection(self):
        """Get classes collection."""
        return self._database["classes"]

    def _get_users_collection(self):
        """Get users collection."""
        return self._database["users"]

    def _get_violations_collection(self):
        """Get violations collection."""
        return self._database["violations"]
