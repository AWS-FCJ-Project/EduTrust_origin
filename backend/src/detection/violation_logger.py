import os
from datetime import datetime, timezone

from bson import ObjectId
from src.utils.s3_utils import get_s3_handler


class ViolationLogger:
    def __init__(self, base_path):
        self.base_path = base_path
        self.s3_handler = get_s3_handler()

    async def log_violation(
        self, exam_id, student_id, violation_type, timestamp=None, metadata=None
    ):
        """Logs a violation and syncs evidence from S3 to MongoDB"""
        from src.database import (
            classes_collection,
            users_collection,
            violations_collection,
        )

        s3_prefix = f"violations/students/{student_id}/{exam_id}/"

        try:
            from src.database import exams_collection

            student = await users_collection.find_one({"_id": ObjectId(student_id)})

            exam = None
            try:
                exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
            except:
                exam = await exams_collection.find_one({"_id": exam_id})

            class_id = "unknown"
            subject_name = "N/A"

            if student:
                if student.get("class_id"):
                    class_id = str(student.get("class_id"))
                else:
                    class_info = await classes_collection.find_one(
                        {
                            "name": student.get("class_name"),
                            "grade": student.get("grade"),
                        }
                    )
                    if class_info:
                        class_id = str(class_info["_id"])

            if exam:
                subject_name = exam.get("subject", "N/A")

            evidence_images = []
            try:
                from src.utils.s3_utils import get_s3_handler

                s3 = get_s3_handler()
                response = s3.s3_client.list_objects_v2(
                    Bucket=s3.bucket_name, Prefix=s3_prefix
                )
                if "Contents" in response:
                    evidence_images = [
                        obj["Key"]
                        for obj in response["Contents"]
                        if obj["Key"].lower().endswith((".jpg", ".jpeg", ".png"))
                    ]
            except Exception as e:
                print(f"[S3 ERROR] Failed to list evidence images: {e}")

            await violations_collection.update_one(
                {"exam_id": str(exam_id), "student_id": str(student_id)},
                {
                    "$set": {
                        "class_id": class_id,
                        "subject": subject_name,
                        "type": violation_type,
                        "timestamp": timestamp
                        or datetime.now(timezone.utc).isoformat(),
                        "violation_time": timestamp
                        or datetime.now(timezone.utc).isoformat(),
                        "evidence_images": evidence_images,
                        "metadata": metadata or {},
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
            print(
                f"[DB SUCCESS] Logged/Updated violation for student {student_id} on S3 (Subject: {subject_name})"
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to sync violation to MongoDB: {e}")

        print(
            f"[SUCCESS] Violation recorded for student {student_id} in exam {exam_id} (Cloud Storage)"
        )


def get_violation_logger():
    return ViolationLogger(None)
