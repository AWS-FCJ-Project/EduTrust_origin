import io
from datetime import datetime, timezone
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from src.auth.auth_utils import hash_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.database import classes_collection, users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserRegister, UserRole

router = APIRouter()


@router.post(
    "/register",
    responses={
        400: {"description": "Email already registered"},
        429: {"description": "Too Many Requests"},
    },
)
@limiter.limit("5/minute")
async def register(request: Request, user: UserRegister):
    del request
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    default_name = user.email.split("@", 1)[0]
    name = (user.name or "").strip() or default_name

    try:
        cognito_user = cognito_auth_service.ensure_user(
            user.email,
            user.password,
            name=name,
            role=(user.role or UserRole.student).value,
        )
    except CognitoAuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)

    if user.role == UserRole.student and user.class_name and user.grade:
        existing_class = await classes_collection.find_one(
            {"name": user.class_name, "grade": user.grade}
        )
        if not existing_class:
            await classes_collection.insert_one(
                {
                    "name": user.class_name,
                    "grade": user.grade,
                    "school_year": "2026-2027",
                    "homeroom_teacher_id": None,
                    "subject_teachers": [],
                    "status": "inactive",
                }
            )

    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "is_verified": True,
        "name": name,
        "role": (user.role or UserRole.student).value,
        "class_name": user.class_name if user.role == UserRole.student else None,
        "grade": user.grade if user.role == UserRole.student else None,
        "cognito_sub": cognito_user.get("sub"),
        "created_at": datetime.now(timezone.utc),
    }
    await users_collection.insert_one(user_doc)

    return {"message": "User registered successfully, you can now login."}


@router.post("/multi-register", responses={400: {"description": "Bad Request"}})
@limiter.limit("5/minute")
async def register_bulk(request: Request, file: Annotated[UploadFile, File(...)]):
    del request
    try:
        content = await file.read()
        filename = getattr(file, "filename", "") or ""
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a valid .csv, .xlsx, or .xls file.",
        )

    df.columns = [str(c).lower().strip() for c in df.columns]

    if "email" not in df.columns or "password" not in df.columns:
        raise HTTPException(
            status_code=400, detail="File must contain 'email' and 'password' columns"
        )

    errors = []
    unique_users = {}
    for index, row in df.iterrows():
        row_number = index + 2
        row_email_raw = row["email"]
        row_password_raw = row["password"]

        if pd.isna(row_email_raw) or pd.isna(row_password_raw):
            continue

        row_email = str(row_email_raw).strip()
        row_password = str(row_password_raw).strip()

        if not row_email or not row_password:
            continue

        name_raw = str(row.get("name", row_email.split("@", 1)[0])).strip()
        name = (
            name_raw
            if name_raw and str(name_raw).lower() != "nan"
            else row_email.split("@", 1)[0]
        )

        role_raw = str(row.get("role", "student")).strip().lower()
        role = UserRole.student
        if role_raw == UserRole.admin.value:
            role = UserRole.admin
        elif role_raw == UserRole.teacher.value:
            role = UserRole.teacher

        class_name = (
            str(row.get("class_name", "")).strip()
            if "class_name" in df.columns
            else None
        )
        class_name = (
            class_name if class_name and str(class_name).lower() != "nan" else None
        )

        grade_raw = row.get("grade")
        grade = (
            int(float(grade_raw))
            if pd.notna(grade_raw) and str(grade_raw).lower() != "nan"
            else None
        )

        try:
            valid_user = UserRegister(
                email=row_email,
                password=row_password,
                name=name,
                role=role,
                class_name=class_name if role == UserRole.student else None,
                grade=grade if role == UserRole.student else None,
            )
        except Exception as error:
            err_msg = str(error).split("\n")[0]
            errors.append(f"Row {row_number}: Invalid data - {err_msg}")
            continue

        if valid_user.email in unique_users:
            errors.append(
                f"Row {row_number}: Email {valid_user.email} is duplicated in the file"
            )
            continue

        unique_users[valid_user.email] = (valid_user, row_number)

    existing_emails: set[str] = set()
    if unique_users:
        cursor = users_collection.find(
            {"email": {"$in": list(unique_users.keys())}},
            {"email": 1},
        )
        existing_docs = await cursor.to_list(length=len(unique_users))
        existing_emails = {doc["email"] for doc in existing_docs if "email" in doc}

    docs_to_insert = []
    for email, (valid_user, row_number) in unique_users.items():
        if email in existing_emails:
            errors.append(f"Row {row_number}: Email {email} already registered")
            continue

        hashed = hash_password(valid_user.password)
        try:
            cognito_user = cognito_auth_service.ensure_user(
                valid_user.email,
                valid_user.password,
                name=valid_user.name,
                role=valid_user.role.value,
            )
        except CognitoAuthError as error:
            errors.append(
                f"Row {row_number}: Cognito provisioning failed - {error.message}"
            )
            continue

        if (
            valid_user.role == UserRole.student
            and valid_user.class_name
            and valid_user.grade
        ):
            existing_class = await classes_collection.find_one(
                {"name": valid_user.class_name, "grade": valid_user.grade}
            )
            if not existing_class:
                await classes_collection.insert_one(
                    {
                        "name": valid_user.class_name,
                        "grade": valid_user.grade,
                        "school_year": "2026-2027",
                        "homeroom_teacher_id": None,
                        "subject_teachers": [],
                        "status": "inactive",
                    }
                )

        docs_to_insert.append(
            {
                "email": valid_user.email,
                "hashed_password": hashed,
                "is_verified": True,
                "name": valid_user.name,
                "role": valid_user.role.value,
                "class_name": valid_user.class_name,
                "grade": valid_user.grade,
                "cognito_sub": cognito_user.get("sub"),
                "created_at": datetime.now(timezone.utc),
            }
        )

    if docs_to_insert:
        await users_collection.insert_many(docs_to_insert, ordered=False)

    return {
        "message": f"Registration completed. Successfully registered {len(docs_to_insert)} users.",
        "errors": errors,
    }
