from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

exam_students = Table('exam_students', Base.metadata, Column('exam_id', ForeignKey('exams.id'), primary_key=True), Column('student_id', ForeignKey('students.id'), primary_key=True))
exam_classrooms = Table('exam_classrooms', Base.metadata, Column('exam_id', ForeignKey('exams.id'), primary_key=True), Column('classroom_id', ForeignKey('classrooms.id'), primary_key=True))
class Student(Base):
    __tablename__='students'; id=Column(Integer,primary_key=True); roll_number=Column(String,unique=True,nullable=False); name=Column(String,nullable=False); department=Column(String,nullable=False); year=Column(String); section=Column(String); accessibility_requirement=Column(String)
class Classroom(Base):
    __tablename__='classrooms'; id=Column(Integer,primary_key=True); name=Column(String,unique=True,nullable=False); building=Column(String); floor=Column(String); rows=Column(Integer,nullable=False); columns=Column(Integer,nullable=False); seats=relationship('Seat',cascade='all, delete-orphan',back_populates='classroom')
class Seat(Base):
    __tablename__='seats'; id=Column(Integer,primary_key=True); classroom_id=Column(Integer,ForeignKey('classrooms.id'),nullable=False); row=Column(Integer,nullable=False); column=Column(Integer,nullable=False); available=Column(Boolean,default=True); accessible=Column(Boolean,default=False); front_row=Column(Boolean,default=False); near_door=Column(Boolean,default=False); classroom=relationship('Classroom',back_populates='seats'); __table_args__=(UniqueConstraint('classroom_id','row','column'),)
class Exam(Base):
    __tablename__='exams'; id=Column(Integer,primary_key=True); name=Column(String,nullable=False); scheduled_at=Column(DateTime); students=relationship('Student',secondary=exam_students); classrooms=relationship('Classroom',secondary=exam_classrooms)
class Arrangement(Base):
    __tablename__='seating_arrangements'; id=Column(Integer,primary_key=True); exam_id=Column(Integer,ForeignKey('exams.id'),unique=True); status=Column(String); objective_value=Column(Integer); statistics=Column(Text); assignments=relationship('Assignment',cascade='all, delete-orphan')
class Assignment(Base):
    __tablename__='seat_assignments'; id=Column(Integer,primary_key=True); arrangement_id=Column(Integer,ForeignKey('seating_arrangements.id')); student_id=Column(Integer,ForeignKey('students.id')); seat_id=Column(Integer,ForeignKey('seats.id')); __table_args__=(UniqueConstraint('arrangement_id','student_id'),UniqueConstraint('arrangement_id','seat_id'))
