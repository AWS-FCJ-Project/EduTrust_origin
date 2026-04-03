from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from src.auth.dependencies import get_current_user
from src.deps import get_db_session
from src.models import Class, ClassSubjectTeacher, User, Violation
from src.schemas.school_schemas import ClassCreate, ClassUpdate

router = APIRouter(prefix="/classes", tags=["Classes"])


def _class_to_dict(cls: Class, *, student_count: int, subject_teachers: list[ClassSubjectTeacher]) -> dict:
    return {
        "id": str(cls.id),
        "name": cls.name,
        "grade": cls.grade,
        "school_year": cls.school_year,
        "homeroom_teacher_id": cls.homeroom_teacher_id,
        "subject_teachers": [
            {"teacher_id": st.teacher_id, "subject": st.subject} for st in subject_teachers
        ],
        "student_count": int(student_count),
        "status": cls.status or "inactive",
    }


async def _student_count(session, *, class_name: str, grade: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(User.role == "student", User.class_name == class_name, User.grade == grade)
    )
    return int(result.scalar() or 0)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create classes")

    new_class = class_data.model_dump()
    status_value = "active" if (new_class.get("homeroom_teacher_id") and new_class.get("subject_teachers")) else "inactive"

    cls = Class(
        name=new_class["name"],
        grade=new_class["grade"],
        school_year=new_class["school_year"],
        homeroom_teacher_id=new_class.get("homeroom_teacher_id"),
        status=status_value,
    )
    session.add(cls)
    await session.flush()

    for st in new_class.get("subject_teachers") or []:
        teacher_id = str(st.get("teacher_id") or "").strip()
        subject = str(st.get("subject") or "").strip()
        if not teacher_id or not subject:
            continue
        session.add(ClassSubjectTeacher(class_id=cls.id, teacher_id=teacher_id, subject=subject))

    return {"id": str(cls.id), "message": "Class created successfully"}


@router.get("", response_model=List[dict])
async def get_classes(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    if role == "admin":
        classes_result = await session.execute(select(Class))
        classes = classes_result.scalars().all()
    elif role == "teacher":
        classes_result = await session.execute(
            select(Class)
            .distinct()
            .outerjoin(ClassSubjectTeacher, ClassSubjectTeacher.class_id == Class.id)
            .where(
                (Class.homeroom_teacher_id == user_id)
                | (ClassSubjectTeacher.teacher_id == user_id)
            )
        )
        classes = classes_result.scalars().all()
    elif role == "student":
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if not u_class or not u_grade:
            return []
        classes_result = await session.execute(
            select(Class).where(Class.name == u_class, Class.grade == int(u_grade))
        )
        classes = classes_result.scalars().all()
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    payload: list[dict] = []
    for cls in classes:
        st_rows = (await session.execute(select(ClassSubjectTeacher).where(ClassSubjectTeacher.class_id == cls.id))).scalars().all()
        payload.append(
            _class_to_dict(
                cls,
                student_count=await _student_count(session, class_name=cls.name, grade=cls.grade),
                subject_teachers=st_rows,
            )
        )
    return payload


@router.get("/homeroom/violations", response_model=List[dict])
async def get_homeroom_violations(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    user_id = str(current_user["_id"])
    cls_res = await session.execute(select(Class).where(Class.homeroom_teacher_id == user_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        return []

    violations_res = await session.execute(select(Violation).where(Violation.class_id == cls.id))
    violations = violations_res.scalars().all()
    payload: list[dict] = []
    for v in violations:
        student_res = await session.execute(select(User).where(User.id == v.student_id))
        student = student_res.scalar_one_or_none()
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
                "student_name": student.name if student else "Unknown",
            }
        )
    return payload


@router.get("/{class_id}", response_model=dict)
async def get_class(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    del current_user
    res = await session.execute(select(Class).where(Class.id == class_id))
    cls = res.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    st_rows = (await session.execute(select(ClassSubjectTeacher).where(ClassSubjectTeacher.class_id == cls.id))).scalars().all()
    return _class_to_dict(
        cls,
        student_count=await _student_count(session, class_name=cls.name, grade=cls.grade),
        subject_teachers=st_rows,
    )


@router.patch("/{class_id}")
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update classes")

    update_data_filtered = {
        k: v
        for k, v in class_data.model_dump().items()
        if v is not None
        and str(v).strip() != ""
        and str(v).lower() != "string"
        and not (k == "grade" and v == 0)
    }
    if not update_data_filtered:
        return {"message": "No changes provided"}

    current_res = await session.execute(select(Class).where(Class.id == class_id))
    current_class = current_res.scalar_one_or_none()
    if not current_class:
        raise HTTPException(status_code=404, detail="Class not found")

    if "subject_teachers" in update_data_filtered:
        subject_teachers = update_data_filtered.pop("subject_teachers") or []
        await session.execute(
            update(Class).where(Class.id == class_id).values(**update_data_filtered)
        )
        await session.execute(
            ClassSubjectTeacher.__table__.delete().where(ClassSubjectTeacher.class_id == class_id)
        )
        for st in subject_teachers:
            teacher_id = str(st.get("teacher_id") or "").strip()
            subject = str(st.get("subject") or "").strip()
            if teacher_id and subject:
                session.add(ClassSubjectTeacher(class_id=class_id, teacher_id=teacher_id, subject=subject))
    else:
        await session.execute(update(Class).where(Class.id == class_id).values(**update_data_filtered))

    # recompute status
    merged_homeroom = update_data_filtered.get("homeroom_teacher_id", current_class.homeroom_teacher_id)
    st_count = await session.execute(select(func.count()).select_from(ClassSubjectTeacher).where(ClassSubjectTeacher.class_id == class_id))
    merged_has_subjects = int(st_count.scalar() or 0) > 0
    status_value = "active" if (merged_homeroom and merged_has_subjects) else "inactive"
    await session.execute(update(Class).where(Class.id == class_id).values(status=status_value))

    return {"message": "Class updated successfully"}


@router.get("/{class_id}/students", response_model=List[dict])
async def get_class_students(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    del current_user
    cls_res = await session.execute(select(Class).where(Class.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    users_res = await session.execute(
        select(User).where(
            User.role == "student", User.class_name == cls.name, User.grade == cls.grade
        )
    )
    from src.routers.auth.login import _user_row_to_dict  # reuse helper
    return [user_helper(_user_row_to_dict(s)) for s in users_res.scalars().all()]


@router.get("/students/available", response_model=List[dict])
async def get_available_students(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    del current_user
    cls_res = await session.execute(select(Class).where(Class.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    users_res = await session.execute(
        select(User).where(
            User.role == "student",
            (User.class_name != cls.name) | (User.grade != cls.grade),
        )
    )
    from src.routers.auth.login import _user_row_to_dict
    return [user_helper(_user_row_to_dict(s)) for s in users_res.scalars().all()]


@router.post("/{class_id}/students/{student_id}")
async def add_student_to_class(
    class_id: str,
    student_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign students")

    cls_res = await session.execute(select(Class).where(Class.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    await session.execute(
        update(User)
        .where(User.id == student_id, User.role == "student")
        .values(class_name=cls.name, grade=cls.grade)
    )
    return {"message": f"Student added to class {cls.name}"}


@router.delete("/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove students")

    del class_id
    await session.execute(
        update(User)
        .where(User.id == student_id, User.role == "student")
        .values(class_name=None, grade=None)
    )
    return {"message": "Student removed from class"}


@router.delete("/{class_id}")
async def delete_class(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete classes")

    cls_res = await session.execute(select(Class).where(Class.id == class_id))
    cls = cls_res.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    await session.execute(
        update(User)
        .where(User.role == "student", User.class_name == cls.name, User.grade == cls.grade)
        .values(class_name=None, grade=None)
    )

    await session.execute(ClassSubjectTeacher.__table__.delete().where(ClassSubjectTeacher.class_id == class_id))
    await session.execute(Class.__table__.delete().where(Class.id == class_id))

    return {
        "message": f"Class {cls.name} and student associations cleared successfully"
    }
