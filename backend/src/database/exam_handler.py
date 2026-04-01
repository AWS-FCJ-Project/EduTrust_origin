import secrets
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo.database import Database
from src.database.db_handler import DBHandler


class ExamHandler(DBHandler):
    """Handler for exam operations using sync pymongo."""

    def __init__(self, database: Database):
        super().__init__(database, "exams")
        self._database = database

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
            exam_dict = self._format_exam(exam_document)
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
            exams.append(self._format_exam(exam_document))
        return exams

    def get_all_exams(self) -> list[dict]:
        """Get all exams for admin."""
        exams = []
        for exam_document in self.collection.find({}):
            exams.append(self._format_exam(exam_document))
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

    def _format_exam(self, exam_document: dict, include_secret: bool = False) -> dict:
        """Helper to format exam document."""
        result = {
            "id": str(exam_document["_id"]),
            "title": exam_document["title"],
            "description": exam_document.get("description"),
            "subject": exam_document["subject"],
            "exam_type": exam_document.get("exam_type", "15-minute quiz"),
            "teacher_id": exam_document["teacher_id"],
            "class_id": exam_document["class_id"],
            "start_time": exam_document["start_time"],
            "end_time": exam_document["end_time"],
            "duration": exam_document.get("duration", 60),
            "has_secret_key": bool(exam_document.get("secret_key")),
            "questions": exam_document.get("questions", []),
        }
        if include_secret:
            result["secret_key"] = exam_document.get("secret_key")
        return result
