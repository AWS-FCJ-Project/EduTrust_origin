import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


async def force_sync():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]

    # Init S3 Handler
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from src.utils.s3_utils import get_s3_handler

    s3 = get_s3_handler()

    print("=== STARTING FORCED SYNC ===")

    async for v in db.violations.find():
        student_id = v.get("student_id")
        exam_id = v.get("exam_id")
        doc_id = v["_id"]

        s3_prefix = f"violations/students/{student_id}/{exam_id}/"
        response = s3.s3_client.list_objects_v2(Bucket=s3.bucket_name, Prefix=s3_prefix)

        evidence_images = []
        if "Contents" in response:
            evidence_images = [
                obj["Key"]
                for obj in response["Contents"]
                if obj["Key"].lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            if len(evidence_images) >= 4:
                print(
                    f"[FORCE REPAIR] Pushing {len(evidence_images)} images into DB for student {student_id} / exam {exam_id}"
                )
                await db.violations.update_one(
                    {"_id": doc_id}, {"$set": {"evidence_images": evidence_images}}
                )

    print("=== FORCE SYNC COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(force_sync())
