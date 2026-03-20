import io
from datetime import datetime, timezone
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from src.auth.auth_utils import hash_password
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserRegister

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
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "is_verified": True,
        "created_at": datetime.now(timezone.utc),
    }
    await users_collection.insert_one(user_doc)

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

    errors = []
    unique_users: dict[str, tuple[str, int]] = {}
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

        try:
            valid_user = UserRegister(email=row_email, password=row_password)
        except Exception as e:
            err_msg = str(e).split("\n")[0]
            errors.append(f"Row {row_number}: Invalid data - {err_msg}")
            continue

        if valid_user.email in unique_users:
            errors.append(
                f"Row {row_number}: Email {valid_user.email} is duplicated in the file"
            )
            continue

        unique_users[valid_user.email] = (valid_user.password, row_number)

    existing_emails: set[str] = set()
    if unique_users:
        cursor = users_collection.find(
            {"email": {"$in": list(unique_users.keys())}},
            {"email": 1},
        )
        existing_docs = await cursor.to_list(length=len(unique_users))
        existing_emails = {doc["email"] for doc in existing_docs if "email" in doc}

    docs_to_insert = []
    for email, (password, row_number) in unique_users.items():
        if email in existing_emails:
            errors.append(f"Row {row_number}: Email {email} already registered")
            continue

        hashed = hash_password(password)
        docs_to_insert.append(
            {
                "email": email,
                "hashed_password": hashed,
                "is_verified": True,
                "created_at": datetime.now(timezone.utc),
            }
        )

    if docs_to_insert:
        await users_collection.insert_many(docs_to_insert, ordered=False)

    return {
        "message": f"Registration completed. Successfully registered {len(docs_to_insert)} users.",
        "errors": errors,
    }
