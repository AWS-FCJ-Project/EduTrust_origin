import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


async def check():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]

    print("VIOLATIONS:")
    count = 0
    async for v in db.violations.find():
        count += 1
        print(f"sid: {v.get('student_id')}")
        print(f"eid: {v.get('exam_id')}")
        print(f"cid: {v.get('class_id')}")
        print(f"sub: {v.get('subject')}")
        imgs = v.get("evidence_images", [])
        print(f"img: {len(imgs)}")
        print("--")
    if count == 0:
        print("NONE")

    print("")
    print("CLASSES:")
    async for cls in db.classes.find():
        cid = str(cls["_id"])
        hr = cls.get("homeroom_teacher_id")
        n = cls.get("name")
        print(f"id:{cid} hr:{hr} n:{n}")

    print("")
    print("STUDENT1:")
    s = await db.users.find_one({"email": "studenttest2@gmail.com"})
    if s:
        print(f"id: {s['_id']}")
        print(f"cid: {s.get('class_id')}")
        print(f"cn: {s.get('class_name')}")
        print(f"gr: {s.get('grade')}")

    print("")
    print("TEACHER:")
    t = await db.users.find_one({"email": "Teacher@gmail.com"})
    if t:
        print(f"id: {t['_id']}")


asyncio.run(check())
