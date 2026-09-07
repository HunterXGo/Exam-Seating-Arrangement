"""Create a realistic, non-destructive sample dataset for ExamFlow.

Run from the backend directory:
    python sample_data.py
"""
from datetime import datetime

from app.database import Base, SessionLocal, engine
from app.models import Classroom, Exam, Seat, Student

Base.metadata.create_all(engine)

BRANCHES = [
    ("CSE", "Computer Science", "Data Structures"),
    ("ECE", "Electronics & Communication", "Digital Electronics"),
    ("ME", "Mechanical Engineering", "Thermodynamics"),
    ("CIV", "Civil Engineering", "Structural Analysis"),
]
FIRST_NAMES = ["Aanya", "Rohan", "Kavya", "Arjun", "Priya", "Aditya", "Sana", "Vikram", "Isha", "Rahul"]
LAST_NAMES = ["Sharma", "Mehta", "Iyer", "Nair", "Singh", "Rao", "Khan", "Patel", "Das", "Verma"]


def get_or_create_room(db, name, building, floor):
    room = db.query(Classroom).filter_by(name=name).first()
    if room:
        return room
    room = Classroom(name=name, building=building, floor=floor, rows=5, columns=10)
    db.add(room)
    db.flush()
    for row in range(1, 6):
        for column in range(1, 11):
            db.add(Seat(
                classroom_id=room.id, row=row, column=column,
                available=True, accessible=(row == 1 and column in (1, 10)),
                front_row=(row == 1), near_door=(row == 5 and column in (9, 10)),
            ))
    return room


def main():
    db = SessionLocal()
    try:
        rooms = [
            get_or_create_room(db, "Engineering Hall A", "Engineering Block", "1"),
            get_or_create_room(db, "Engineering Hall B", "Engineering Block", "2"),
        ]
        db.flush()
        all_by_branch = {}
        for branch_index, (code, department, subject) in enumerate(BRANCHES):
            students = []
            for number in range(1, 26):
                roll = f"{code}26{number:03d}"
                student = db.query(Student).filter_by(roll_number=roll).first()
                if not student:
                    student = Student(
                        roll_number=roll,
                        name=f"{FIRST_NAMES[(number - 1) % 10]} {LAST_NAMES[(number + branch_index) % 10]}",
                        department=department,
                        year="2",
                        section="A" if number <= 13 else "B",
                        accessibility_requirement="wheelchair" if code == "CSE" and number == 1 else None,
                    )
                    db.add(student)
                students.append(student)
            db.flush()
            all_by_branch[code] = students
            exam_name = f"{subject} — {code} Midterm"
            exam = db.query(Exam).filter_by(name=exam_name).first()
            if not exam:
                exam = Exam(
                    name=exam_name,
                    scheduled_at=datetime(2026, 9, 10 + branch_index, 10, 0),
                    students=students,
                    classrooms=rooms,
                )
                db.add(exam)
        db.commit()
        print("Sample data ready: 100 students, 2 classrooms (100 seats), 4 subject exams.")
        for code, _, subject in BRANCHES:
            print(f"  {subject} — {code} Midterm: {len(all_by_branch[code])} students")
    finally:
        db.close()


if __name__ == "__main__":
    main()
