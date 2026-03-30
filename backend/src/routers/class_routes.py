from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from src.auth.dependencies import get_current_user
from src.database import classes_collection, users_collection, violations_collection
from src.schemas.school_schemas import ClassCreate, ClassResponse, ClassUpdate

router = APIRouter(prefix="/classes", tags=["Classes"])


async def class_helper(cls) -> dict:
    student_count = await users_collection.count_documents(
        {"role": "student", "class_name": cls["name"], "grade": cls["grade"]}
    )

    return {
        "id": str(cls["_id"]),
        "name": cls["name"],
        "grade": cls["grade"],
        "school_year": cls["school_year"],
        "homeroom_teacher_id": cls.get("homeroom_teacher_id"),
        "subject_teachers": cls.get("subject_teachers", []),
        "student_count": student_count,
        "status": cls.get("status", "inactive"),
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate, current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create classes")

    new_class = class_data.model_dump()
    if new_class.get("homeroom_teacher_id") and new_class.get("subject_teachers"):
        new_class["status"] = "active"
    else:
        new_class["status"] = "inactive"

    result = await classes_collection.insert_one(new_class)
    return {"id": str(result.inserted_id), "message": "Class created successfully"}


@router.get("", response_model=List[dict])
async def get_classes(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    query = {}
    if role == "admin":
        query = {}
    elif role == "teacher":
        query = {
            "$or": [
                {"homeroom_teacher_id": user_id},
                {"subject_teachers.teacher_id": user_id},
            ]
        }
    elif role == "student":
        u_class = current_user.get("class_name")
        u_grade = current_user.get("grade")
        if not u_class or not u_grade:
            return []
        query = {"name": u_class, "grade": u_grade}
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    classes = []
    async for cls in classes_collection.find(query):
        classes.append(await class_helper(cls))
    return classes


@router.get("/teachers", response_model=List[dict])
async def list_teachers(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    teachers = []
    async for t in users_collection.find({"role": "teacher"}):
        t_id = str(t["_id"])
        assigned_classes = []

        async for c in classes_collection.find({"homeroom_teacher_id": t_id}):
            assigned_classes.append(
                {"id": str(c["_id"]), "name": c["name"], "role": "Homeroom Teacher"}
            )

        async for c in classes_collection.find({"subject_teachers.teacher_id": t_id}):
            for st in c.get("subject_teachers", []):
                if st["teacher_id"] == t_id:
                    assigned_classes.append(
                        {
                            "id": str(c["_id"]),
                            "name": c["name"],
                            "role": f"Subject Teacher ({st.get('subject', 'N/A')})",
                        }
                    )

        teachers.append(
            {
                "id": t_id,
                "name": t.get("name"),
                "email": t["email"],
                "subjects": t.get("subjects", []),
                "password_plain": t.get("password_plain"),
                "assigned_classes": assigned_classes,
                "is_assigned": len(assigned_classes) > 0,
            }
        )
    return teachers


@router.get("/admins", response_model=List[dict])
async def list_admins(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    admins = []
    async for a in users_collection.find({"role": "admin"}):
        admins.append(
            {
                "id": str(a["_id"]),
                "name": a.get("name"),
                "email": a["email"],
                "password_plain": a.get("password_plain"),
            }
        )
    return admins


@router.get("/homeroom/violations", response_model=List[dict])
async def get_homeroom_violations(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    cls = await classes_collection.find_one({"homeroom_teacher_id": user_id})
    if not cls:
        return []
    class_id = str(cls["_id"])

    violations = []
    async for v in violations_collection.find({"class_id": class_id}):
        v["id"] = str(v["_id"])
        student = await users_collection.find_one(
            {"_id": ObjectId(str(v["student_id"]))}
        )
        v["student_name"] = student["name"] if student else "Unknown"
        violations.append(v)
    return violations


@router.get("/{class_id}", response_model=dict)
async def get_class(class_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    cls = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    return await class_helper(cls)


@router.patch("/{class_id}")
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update classes")

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

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

    current_class = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not current_class:
        raise HTTPException(status_code=404, detail="Class not found")

    merged_class = {**current_class, **update_data_filtered}
    if merged_class.get("homeroom_teacher_id") and merged_class.get("subject_teachers"):
        update_data_filtered["status"] = "active"
    else:
        update_data_filtered["status"] = "inactive"

    result = await classes_collection.update_one(
        {"_id": ObjectId(class_id)}, {"$set": update_data_filtered}
    )
    return {"message": "Class updated successfully"}


@router.get("/{class_id}/students", response_model=List[dict])
async def get_class_students(
    class_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    cls = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    students = []
    async for s in users_collection.find(
        {"role": "student", "class_name": cls["name"], "grade": cls["grade"]}
    ):
        from src.routers.auth.login import user_helper

        students.append(user_helper(s))
    return students


@router.get("/students/available", response_model=List[dict])
async def get_available_students(
    class_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    cls = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    students = []
    async for s in users_collection.find(
        {
            "role": "student",
            "$or": [
                {"class_name": {"$ne": cls["name"]}},
                {"grade": {"$ne": cls["grade"]}},
            ],
        }
    ):
        from src.routers.auth.login import user_helper

        students.append(user_helper(s))
    return students


@router.post("/{class_id}/students/{student_id}")
async def add_student_to_class(
    class_id: str, student_id: str, current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign students")

    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid IDs")

    cls = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    result = await users_collection.update_one(
        {"_id": ObjectId(student_id), "role": "student"},
        {"$set": {"class_name": cls["name"], "grade": cls["grade"]}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    return {"message": f"Student added to class {cls['name']}"}


@router.delete("/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: str, student_id: str, current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove students")

    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid IDs")

    result = await users_collection.update_one(
        {"_id": ObjectId(student_id), "role": "student"},
        {"$set": {"class_name": None, "grade": None}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    return {"message": "Student removed from class"}


@router.delete("/{class_id}")
async def delete_class(class_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete classes")

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    cls = await classes_collection.find_one({"_id": ObjectId(class_id)})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    await users_collection.update_many(
        {"role": "student", "class_name": cls["name"], "grade": cls["grade"]},
        {"$set": {"class_name": None, "grade": None}},
    )

    await classes_collection.delete_one({"_id": ObjectId(class_id)})

    return {
        "message": f"Class {cls['name']} and student associations cleared successfully"
    }
