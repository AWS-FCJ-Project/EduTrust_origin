from typing import Optional

from bson import ObjectId
from pymongo.database import Database
from src.database.db_handler import DBHandler


class ClassHandler(DBHandler):
    """Handler for class operations using sync pymongo."""

    def __init__(self, database: Database):
        super().__init__(database, "classes")
        self._database = database

    def create_class(self, class_data: dict) -> str:
        """Create a new class."""
        new_class = class_data.copy()
        if new_class.get("homeroom_teacher_id") and new_class.get("subject_teachers"):
            new_class["status"] = "active"
        else:
            new_class["status"] = "inactive"

        result = self.collection.insert_one(new_class)
        return str(result.inserted_id)

    def get_class_by_id(self, class_id: str) -> Optional[dict]:
        """Get class by ID."""
        if not ObjectId.is_valid(class_id):
            return None
        return self.collection.find_one({"_id": ObjectId(class_id)})

    def get_classes_for_teacher(self, teacher_id: str) -> list[dict]:
        """Get classes where teacher is homeroom or subject teacher."""
        classes = []
        for cls in self.collection.find(
            {
                "$or": [
                    {"homeroom_teacher_id": teacher_id},
                    {"subject_teachers.teacher_id": teacher_id},
                ]
            }
        ):
            classes.append(self._class_helper(cls))
        return classes

    def get_classes_for_student(self, class_name: str, grade: str) -> list[dict]:
        """Get classes for a student."""
        classes = []
        for cls in self.collection.find({"name": class_name, "grade": grade}):
            classes.append(self._class_helper(cls))
        return classes

    def get_all_classes(self) -> list[dict]:
        """Get all classes for admin."""
        classes = []
        for cls in self.collection.find({}):
            classes.append(self._class_helper(cls))
        return classes

    def update_class(self, class_id: str, update_data: dict) -> bool:
        """Update a class."""
        if not ObjectId.is_valid(class_id):
            return False

        filtered = {
            k: v
            for k, v in update_data.items()
            if v is not None
            and str(v).strip() != ""
            and str(v).lower() != "string"
            and not (k == "grade" and v == 0)
        }

        if not filtered:
            return False

        current = self.collection.find_one({"_id": ObjectId(class_id)})
        if not current:
            return False

        merged = {**current, **filtered}
        if merged.get("homeroom_teacher_id") and merged.get("subject_teachers"):
            filtered["status"] = "active"
        else:
            filtered["status"] = "inactive"

        result = self.collection.update_one(
            {"_id": ObjectId(class_id)}, {"$set": filtered}
        )
        return result.modified_count > 0

    def delete_class(self, class_id: str) -> bool:
        """Delete a class and clear student associations."""
        if not ObjectId.is_valid(class_id):
            return False

        cls = self.collection.find_one({"_id": ObjectId(class_id)})
        if not cls:
            return False

        # Clear student associations
        self._users_collection().update_many(
            {"role": "student", "class_name": cls["name"], "grade": cls["grade"]},
            {"$set": {"class_name": None, "grade": None}},
        )

        result = self.collection.delete_one({"_id": ObjectId(class_id)})
        return result.deleted_count > 0

    def add_student(self, class_id: str, student_id: str) -> bool:
        """Add a student to a class."""
        if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
            return False

        cls = self.collection.find_one({"_id": ObjectId(class_id)})
        if not cls:
            return False

        result = self._users_collection().update_one(
            {"_id": ObjectId(student_id), "role": "student"},
            {"$set": {"class_name": cls["name"], "grade": cls["grade"]}},
        )
        return result.matched_count > 0

    def remove_student(self, class_id: str, student_id: str) -> bool:
        """Remove a student from a class."""
        if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
            return False

        result = self._users_collection().update_one(
            {"_id": ObjectId(student_id), "role": "student"},
            {"$set": {"class_name": None, "grade": None}},
        )
        return result.matched_count > 0

    def get_students(self, class_id: str) -> list[dict]:
        """Get all students in a class."""
        if not ObjectId.is_valid(class_id):
            return []

        cls = self.collection.find_one({"_id": ObjectId(class_id)})
        if not cls:
            return []

        students = []
        for s in self._users_collection().find(
            {"role": "student", "class_name": cls["name"], "grade": cls["grade"]}
        ):
            students.append(self._user_helper(s))
        return students

    def get_violations(self, class_id: str) -> list[dict]:
        """Get all violations for a class."""
        violations = []
        for v in self._violations_collection().find({"class_id": class_id}):
            v["id"] = str(v["_id"])
            student = self._users_collection().find_one(
                {"_id": ObjectId(str(v["student_id"]))}
            )
            v["student_name"] = student["name"] if student else "Unknown"
            violations.append(v)
        return violations

    def get_available_students(self, class_id: str) -> list[dict]:
        """Get students not in a class."""
        if not ObjectId.is_valid(class_id):
            return []

        cls = self.collection.find_one({"_id": ObjectId(class_id)})
        if not cls:
            return []

        students = []
        for s in self._users_collection().find(
            {
                "role": "student",
                "$or": [
                    {"class_name": {"$ne": cls["name"]}},
                    {"grade": {"$ne": cls["grade"]}},
                ],
            }
        ):
            students.append(self._user_helper(s))
        return students

    def _users_collection(self):
        """Get users collection."""
        return self._database["users"]

    def _violations_collection(self):
        """Get violations collection."""
        return self._database["violations"]

    def _class_helper(self, cls: dict) -> dict:
        """Helper to format class document."""
        student_count = self._users_collection().count_documents(
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

    def _user_helper(self, user: dict) -> dict:
        """Helper to format user document."""
        return {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "class_name": user.get("class_name"),
            "grade": user.get("grade"),
        }
