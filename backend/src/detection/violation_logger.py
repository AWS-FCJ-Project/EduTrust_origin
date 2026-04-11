from datetime import datetime, timezone
from typing import Optional

_persistence: Optional[object] = None


class ViolationLogger:
    def __init__(self, persistence):
        self._persistence = persistence

    async def log_violation(
        self, exam_id, student_id, violation_type, timestamp=None, metadata=None
    ):
        """Logs a violation and syncs evidence from S3 to DynamoDB"""
        from src.utils.s3_utils import get_s3_handler

        s3_prefix = f"violations/students/{student_id}/{exam_id}/"
        persistence = self._persistence

        try:
            student = await persistence.users.get_by_id(student_id)

            exam = await persistence.exams.get_by_id(exam_id)
            if not exam:
                exam = await persistence.exams.find_one({"_id": exam_id})

            class_id = "unknown"
            subject_name = "N/A"

            if student:
                if student.get("class_id"):
                    class_id = str(student.get("class_id"))
                else:
                    class_info = await persistence.classes.get_by_name_grade(
                        student.get("class_name"),
                        student.get("grade"),
                    )
                    if class_info:
                        class_id = str(class_info["_id"])

            if exam:
                subject_name = exam.get("subject", "N/A")

            evidence_images = []
            try:
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

            await persistence.violations.upsert(
                str(exam_id),
                str(student_id),
                {
                    "class_id": class_id,
                    "subject": subject_name,
                    "type": violation_type,
                    "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
                    "violation_time": timestamp
                    or datetime.now(timezone.utc).isoformat(),
                    "evidence_images": evidence_images,
                    "metadata": metadata or {},
                    "updated_at": datetime.now(timezone.utc),
                    "created_at": datetime.now(timezone.utc),
                },
            )
            print(
                f"[DB SUCCESS] Logged/Updated violation for student {student_id} on S3 (Subject: {subject_name})"
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to sync violation to DynamoDB: {e}")

        print(
            f"[SUCCESS] Violation recorded for student {student_id} in exam {exam_id} (Cloud Storage)"
        )


_violation_logger: Optional[ViolationLogger] = None


def set_violation_logger_persistence(persistence) -> None:
    """Call during app startup to inject persistence into the violation logger."""
    global _violation_logger
    _violation_logger = ViolationLogger(persistence)


def get_violation_logger() -> ViolationLogger:
    """Return the global ViolationLogger instance. Call set_violation_logger_persistence first."""
    if _violation_logger is None:
        raise RuntimeError(
            "ViolationLogger not initialized. "
            "Call set_violation_logger_persistence() during app startup."
        )
    return _violation_logger
