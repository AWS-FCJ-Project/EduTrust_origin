import io
from datetime import datetime, timezone
from typing import Annotated, Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from src.auth.auth_utils import hash_password
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserRegister

router = APIRouter()


@router.post("/register", responses={400: {"description": "Bad Request"}})
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

    added = 0
    errors = []
    for index, row in df.iterrows():
        row_email = str(row["email"]).strip()
        row_password = str(row["password"]).strip()

        if (
            not row_email
            or not row_password
            or row_email == "nan"
            or row_password == "nan"
        ):
            continue

        try:
            valid_user = UserRegister(email=row_email, password=row_password)
        except Exception as e:
            err_msg = str(e).split("\n")[0]
            errors.append(f"Row {index+2}: Invalid data - {err_msg}")
            continue

        existing = await users_collection.find_one({"email": valid_user.email})
        if existing:
            errors.append(f"Row {index+2}: Email {valid_user.email} already registered")
            continue

        hashed = hash_password(valid_user.password)
        user_doc = {
            "email": valid_user.email,
            "hashed_password": hashed,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
        }
        await users_collection.insert_one(user_doc)
        added += 1

    return {
        "message": f"Registration completed. Successfully registered {added} users.",
        "errors": errors,
    }
