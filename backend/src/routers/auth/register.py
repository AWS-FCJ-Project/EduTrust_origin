import asyncio
import io
from datetime import datetime, timezone
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from src.auth.auth_utils import hash_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.extensions import limiter
from src.schemas.auth_schemas import UserRegister, UserRole
from src.utils.s3_utils import get_s3_handler

router = APIRouter()

# Bounded concurrency limit for DB operations
MAX_CONCURRENT_DB_OPS = 10


@router.post(
    "/register",
    responses={
        400: {"description": "Email already registered"},
        429: {"description": "Too Many Requests"},
    },
)
@limiter.limit("5/minute")
async def register(request: Request, user: UserRegister):
    persistence = request.app.state.persistence
    existing = await persistence.users.get_by_email(user.email)
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
        existing_class = await persistence.classes.get_by_name_grade(
            user.class_name, user.grade
        )
        if not existing_class:
            await persistence.classes.insert_one(
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
        "avatar": None,
    }

    # Handle avatar: base64 → S3, otherwise store directly
    if user.avatar:
        if user.avatar.startswith("data:image"):
            try:
                import base64

                # Parse data URL: data:image/png;base64,<base64>
                header, data = user.avatar.split(",", 1)
                content_type = header.split(";")[0].replace(
                    "data:", ""
                )  # e.g. "image/png"
                image_bytes = base64.b64decode(data)

                # Generate unique S3 key
                s3_key = f"avatars/{cognito_user.get('sub', user.email.split('@')[0])}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.jpg"

                # Upload to S3
                s3 = get_s3_handler()
                uploaded = s3.upload_file_bytes(image_bytes, s3_key, content_type)
                if uploaded:
                    # Store S3 key (not presigned URL) - URL will be generated at read time
                    user_doc["avatar"] = s3_key
            except Exception as e:
                print(f"[AVATAR ERROR] Failed to upload avatar: {e}")
                # Continue without avatar if upload fails
        else:
            # Store direct URL (forward compatibility)
            user_doc["avatar"] = user.avatar

    await persistence.users.insert_one(user_doc)

    return {"message": "User registered successfully, you can now login."}


@router.post("/multi-register", responses={400: {"description": "Bad Request"}})
@limiter.limit("5/minute")
async def register_bulk(request: Request, file: Annotated[UploadFile, File(...)]):
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

    persistence = request.app.state.persistence
    errors = []
    unique_users = {}
    for index, row in df.iterrows():
        row_number = int(index) + 2
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

        # Avatar: base64 data URL or image URL (optional)
        avatar_raw = row.get("avatar")
        avatar_value = None
        if (
            pd.notna(avatar_raw)
            and str(avatar_raw).lower() != "nan"
            and str(avatar_raw).strip()
        ):
            avatar_value = str(avatar_raw).strip()

        try:
            valid_user = UserRegister(
                email=row_email,
                password=row_password,
                name=name,
                role=role,
                class_name=class_name if role == UserRole.student else None,
                grade=grade if role == UserRole.student else None,
                avatar=avatar_value,
            )
        except Exception as e:
            err_msg = str(e).split("\n")[0]
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
        # Bounded concurrency for email checks
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DB_OPS)

        async def check_email(email: str) -> tuple[str, bool]:
            async with semaphore:
                existing = await persistence.users.get_by_email(email)
                return email, existing is not None

        results = await asyncio.gather(
            *[check_email(email) for email in unique_users.keys()]
        )
        for email, exists in results:
            if exists:
                existing_emails.add(email)

    docs_to_insert = []
    for email, (valid_user, row_number) in unique_users.items():
        if email in existing_emails:
            errors.append(f"Row {row_number}: Email {email} already registered")
            continue

        hashed = hash_password(valid_user.password)

        if (
            valid_user.role == UserRole.student
            and valid_user.class_name
            and valid_user.grade
        ):
            existing_class = await persistence.classes.get_by_name_grade(
                valid_user.class_name, valid_user.grade
            )
            if not existing_class:
                await persistence.classes.insert_one(
                    {
                        "name": valid_user.class_name,
                        "grade": valid_user.grade,
                        "school_year": "2026-2027",
                        "homeroom_teacher_id": None,
                        "subject_teachers": [],
                        "status": "inactive",
                    }
                )

        try:
            cognito_user = cognito_auth_service.ensure_user(
                valid_user.email,
                valid_user.password,
                name=valid_user.name,
                role=valid_user.role.value,
            )
        except CognitoAuthError as error:
            errors.append(f"Row {row_number}: {error.message}")
            continue

        # Build user doc, handle avatar if base64
        user_doc = {
            "email": valid_user.email,
            "hashed_password": hashed,
            "is_verified": True,
            "name": valid_user.name,
            "role": valid_user.role.value,
            "class_name": valid_user.class_name,
            "grade": valid_user.grade,
            "cognito_sub": cognito_user.get("sub"),
            "created_at": datetime.now(timezone.utc),
            "avatar": None,
        }

        # Handle avatar: base64 → S3, otherwise store directly
        if valid_user.avatar:
            if valid_user.avatar.startswith("data:image"):
                try:
                    import base64

                    header, data = valid_user.avatar.split(",", 1)
                    content_type = header.split(";")[0].replace("data:", "")
                    image_bytes = base64.b64decode(data)
                    s3_key = f"avatars/{cognito_user.get('sub', valid_user.email.split('@')[0])}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.jpg"
                    s3 = get_s3_handler()
                    uploaded = s3.upload_file_bytes(image_bytes, s3_key, content_type)
                    if uploaded:
                        # Store S3 key (not presigned URL) - URL will be generated at read time
                        user_doc["avatar"] = s3_key
                except Exception as e:
                    print(f"[AVATAR ERROR] Row {row_number}: {e}")
            else:
                # Store direct URL (forward compatibility)
                user_doc["avatar"] = valid_user.avatar

        docs_to_insert.append(user_doc)

    if docs_to_insert:
        # Batch write users
        await persistence.users.insert_many(docs_to_insert)

    return {
        "message": f"Registration completed. Successfully registered {len(docs_to_insert)} users.",
        "errors": errors,
    }
