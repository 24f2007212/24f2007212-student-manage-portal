from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum


class Role(Enum):
    ADMIN = "admin"
    EXAMINER = "examiner"
    STUDENT = "student"
class CourseStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
class ExamType(Enum):
    VIVA = "Viva"
    PRACTICAL = "Practical"
    PROJECT_DEMO = "Project Demo"
    ASSESSMENT = "Assessment"
class ExamStatus(Enum):
    DRAFT = "Draft"
    SLOT_CREATION = "Slot Creation"
    BOOKING_OPEN = "Booking Open"
    CLOSED = "Closed"
    COMPLETED = "Completed"
class SlotStatus(Enum):
    AVAILABLE = "Available"
    FULL = "Full"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
class BookingStatus(Enum):
    BOOKED = "Booked"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"

db = SQLAlchemy()

#one table for admin, examiner and student (role decides who is who)
class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
    db.CheckConstraint(
        "length(phone) = 10",
        name="check_phone_length"
    ),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    approved = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, default=True)#admin can deactivate examiners
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(
    db.Enum(Role),
    nullable=False
    )
    #relations
    #examiner extra details (one to one)
    examiner_profile = db.relationship("ExaminerProfile", backref="user", uselist=False, lazy=True)
    #examiner id and examinations assigned to him
    assigned_exams = db.relationship("Examination", backref="assigned_examiner", lazy=True)
    #examiner id and slots created by him
    slots = db.relationship("ExamSlot", backref="examiner", lazy=True)
    #student id and bookings
    bookings = db.relationship("Booking", backref="student", lazy=True)

#extra details only for examiners
class ExaminerProfile(db.Model):
    __tablename__ = "examiner_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))

#table for courses
class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(
    db.Enum(CourseStatus),
    nullable=False,
    default=CourseStatus.ACTIVE
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #course id and examinations
    examinations = db.relationship("Examination", backref="course", lazy=True, cascade="all, delete-orphan")

#table for examinations
class Examination(db.Model):
    __tablename__ = "examinations"
    __table_args__ = (
    db.CheckConstraint(
        "duration_minutes > 0",
        name="check_duration"
    ),
    db.CheckConstraint(
        "max_marks > 0",
        name="check_max_marks"
    ),
    )
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(
    db.Enum(ExamType),
    nullable=False
    )
    duration_minutes = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    slot_creation_start = db.Column(db.Date, nullable=False)
    slot_creation_end = db.Column(db.Date, nullable=False)
    booking_start = db.Column(db.Date, nullable=False)
    booking_end = db.Column(db.Date, nullable=False)
    status = db.Column(
    db.Enum(ExamStatus),
    nullable=False,
    default=ExamStatus.DRAFT
    )
    #nullable because exam can be in draft without examiner
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    results_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #relations, cascade so deleting exam removes its rubrics, slots and bookings
    rubrics = db.relationship("Rubric", backref="examination", lazy=True, cascade="all, delete-orphan")
    slots = db.relationship("ExamSlot", backref="examination", lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="examination", lazy=True, cascade="all, delete-orphan")

#evaluation criteria for an examination
class Rubric(db.Model):
    __tablename__ = "rubrics"
    __table_args__ = (
    db.CheckConstraint(
        "max_marks > 0",
        name="check_rubric_marks"
    ),
    db.CheckConstraint(
        "weightage > 0",
        name="check_weightage"
    ),
    )
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    criterion_name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

#time slot created by examiner
class ExamSlot(db.Model):
    __tablename__ = "exam_slots"
    __table_args__ = (
    db.CheckConstraint(
        "capacity > 0",
        name="check_capacity"
    ),
    db.CheckConstraint(
        "available_seats >= 0",
        name="check_available_seats_positive"
    ),
    db.CheckConstraint(
        "available_seats <= capacity",
        name="check_available_seats"
    ),
    )
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(
    db.Enum(SlotStatus),
    nullable=False,
    default=SlotStatus.AVAILABLE
    )
    #slot id and bookings
    bookings = db.relationship("Booking", backref="slot", lazy=True)

#student booking a slot
class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (
        #one student can book only one slot per examination
        db.UniqueConstraint(
            "student_id",
            "exam_id",
            name="unique_booking"
        ),
    )
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("exam_slots.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(
    db.Enum(BookingStatus),
    nullable=False,
    default=BookingStatus.BOOKED
    )
    #filled by examiner after evaluation
    total_marks = db.Column(db.Float)
    remarks = db.Column(db.Text)
    evaluated = db.Column(db.Boolean, default=False)
    #marks for each rubric
    evaluations = db.relationship("Evaluation", backref="booking", lazy=True, cascade="all, delete-orphan")

#marks given for one rubric of one booking
class Evaluation(db.Model):
    __tablename__ = "evaluations"
    __table_args__ = (
        db.UniqueConstraint(
            "booking_id",
            "rubric_id",
            name="unique_evaluation"
        ),
        db.CheckConstraint(
            "marks >= 0",
            name="check_marks"
        ),
    )
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey("rubrics.id"), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    rubric = db.relationship("Rubric", lazy=True)
