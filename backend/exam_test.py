import asyncio
import os

from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


async def check():
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    db = client[os.getenv("MONGO_DB_NAME")]

    exam_id = "69c7fcc95ec2849c9f9091e0"
    print("Searching for Exam ID:", exam_id)

    try:
        e1 = await db.exams.find_one({"_id": ObjectId(exam_id)})
        title = e1.get("title") if e1 else ""
        print("Found as ObjectId:", e1 is not None, "| Title:", title)
    except Exception as e:
        print("Error as ObjectId:", e)

    e2 = await db.exams.find_one({"id": exam_id})
    title = e2.get("title") if e2 else ""
    print("Found as String:", e2 is not None, "| Title:", title)


asyncio.run(check())
