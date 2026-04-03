from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update

from src.db import session_scope
from src.models import Class, Exam, User, Violation
from src.utils.s3_utils import get_s3_handler


class ViolationLogger:
    def __init__(self, base_path):
        self.base_path = base_path
        self.s3_handler = get_s3_handler()

    async def log_violation(
        self, exam_id, student_id, violation_type, timestamp=None, metadata=None
    ):
        """Logs a violation and syncs evidence from S3 to RDS."""
        s3_prefix = f"violations/students/{student_id}/{exam_id}/"

        async with session_scope() as session:
            student = (
                (await session.execute(select(User).where(User.id == str(student_id))))
                .scalar_one_or_none()
            )
            exam = (
                (await session.execute(select(Exam).where(Exam.id == str(exam_id))))
                .scalar_one_or_none()
            )

            class_id = "unknown"
            subject_name = "N/A"

            if student:
                # Prefer a canonical class id when possible by looking up class_name+grade.
                if student.class_name and student.grade is not None:
                    class_info = (
                        (
                            await session.execute(
                                select(Class).where(
                                    Class.name == student.class_name,
                                    Class.grade == int(student.grade),
                                )
                            )
                        )
                        .scalar_one_or_none()
                    )
                    if class_info:
                        class_id = str(class_info.id)

            if exam:
                subject_name = exam.subject or "N/A"

            evidence_images: list[str] = []
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
            except Exception:
                evidence_images = []

            now_iso = (timestamp or datetime.now(timezone.utc).isoformat())

            existing = await session.execute(
                select(Violation).where(
                    Violation.exam_id == str(exam_id),
                    Violation.student_id == str(student_id),
                )
            )
            row = existing.scalar_one_or_none()
            if row is None:
                session.add(
                    Violation(
                        exam_id=str(exam_id),
                        student_id=str(student_id),
                        class_id=str(class_id),
                        subject=str(subject_name),
                        type=str(violation_type),
                        timestamp=now_iso,
                        violation_time=now_iso,
                        evidence_images=evidence_images,
                        metadata_=metadata or {},
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            else:
                await session.execute(
                    update(Violation)
                    .where(Violation.id == row.id)
                    .values(
                        class_id=str(class_id),
                        subject=str(subject_name),
                        type=str(violation_type),
                        timestamp=now_iso,
                        violation_time=now_iso,
                        evidence_images=evidence_images,
                        metadata_=metadata or {},
                        updated_at=datetime.now(timezone.utc),
                    )
                )


def get_violation_logger():
    return ViolationLogger(None)
