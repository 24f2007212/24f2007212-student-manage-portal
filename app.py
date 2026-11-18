from flask import Flask,render_template,request,redirect,url_for,flash,session
from models import db,User,Role,ExaminerProfile,Course,Examination,Rubric,ExamSlot,Booking,Evaluation
from models import CourseStatus,ExamType,ExamStatus,SlotStatus,BookingStatus
import os
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime, date

app = Flask(__name__)
app.config["SECRET_KEY"] = "exam-management-portal"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "instance", "exam_portal.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def create_admin():

    admin = User.query.filter_by(role=Role.ADMIN).first()

    if admin is None:

        admin = User(
            name="Admin",
            email="admin@exam.com",
            password_hash=generate_password_hash("admin123"),
            phone="9999999999",
            role=Role.ADMIN,
            approved=True,
            active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin created successfully")

    else:

        print("Admin already exists")

@app.before_request
def check_active_user():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user is None or not user.active:
            session.clear()
            flash("Your account has been deactivated.", "danger")
            return redirect(url_for("login"))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password")
    role = request.form.get("role")
    department = request.form.get("department", "").strip()
    designation = request.form.get("designation", "").strip()

    if not name:
        flash("Name cannot be empty.", "danger")
        return redirect(url_for("register"))
    if not email:
        flash("Email cannot be empty.", "danger")
        return redirect(url_for("register"))
    if not password:
        flash("Password cannot be empty.", "danger")
        return redirect(url_for("register"))
    if not phone.isdigit() or len(phone) != 10:
        flash("Phone number must contain exactly 10 digits.", "danger")
        return redirect(url_for("register"))
    if "@" not in email or "." not in email.split("@")[-1]:
        flash("Please enter a valid email address.", "danger")
        return redirect(url_for("register"))
    if role not in ["EXAMINER", "STUDENT"]:
        flash("Invalid registration role.", "danger")
        return redirect(url_for("register"))
    if role == "EXAMINER" and not department:
        flash("Department is required for examiners.", "danger")
        return redirect(url_for("register"))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already exists.", "danger")
        return redirect(url_for("register"))

    new_user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        phone=phone,
        role=Role[role],
        approved=False if role == "EXAMINER" else True,
        active=True)

    db.session.add(new_user)
    db.session.commit()

    if role == "EXAMINER":
        profile = ExaminerProfile(
            user_id=new_user.id,
            department=department,
            designation=designation
        )
        db.session.add(profile)
        db.session.commit()
        flash("Registration successful. Wait for admin approval before login.", "success")
    else:
        flash("Registration successful. Please login.", "success")

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    if user is None:

        flash("Invalid email.", "danger")
        return redirect(url_for("login"))

    if not check_password_hash(user.password_hash, password):

        flash("Incorrect password.", "danger")
        return redirect(url_for("login"))

    if not user.active:

        flash("Your account has been deactivated.", "danger")
        return redirect(url_for("login"))

    if user.role == Role.EXAMINER and not user.approved:

        flash("Your account is waiting for admin approval.", "warning")
        return redirect(url_for("login"))

    session["user_id"] = user.id
    session["role"] = user.role.name
    session["name"] = user.name

    flash("Login successful.", "success")

    if user.role == Role.ADMIN:
        return redirect(url_for("admin_dashboard"))

    elif user.role == Role.EXAMINER:
        return redirect(url_for("examiner_dashboard"))

    return redirect(url_for("student_dashboard"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    total_courses = Course.query.count()
    total_exams = Examination.query.count()
    total_examiners = User.query.filter_by(role=Role.EXAMINER).count()
    total_students = User.query.filter_by(role=Role.STUDENT).count()
    total_slots = ExamSlot.query.count()
    total_bookings = Booking.query.count()

    courses = Course.query.all()
    exams = Examination.query.all()

    pending_examiners = User.query.filter_by(role=Role.EXAMINER, approved=False).all()

    search = request.args.get("search", "").strip()

    found_users = []
    found_exams = []
    found_bookings = []

    if search:
        found_users = User.query.filter(
            User.role != Role.ADMIN,
            db.or_(User.name.ilike(f"%{search}%"), db.cast(User.id, db.String) == search)
        ).all()

        found_exams = Examination.query.filter(
            db.or_(Examination.exam_name.ilike(f"%{search}%"), db.cast(Examination.id, db.String) == search)
        ).all()

        found_bookings = Booking.query.join(User, Booking.student_id == User.id).filter(
            db.or_(User.name.ilike(f"%{search}%"), db.cast(Booking.id, db.String) == search)
        ).all()

    return render_template(
    "admin_dash.html",
    total_courses=total_courses,total_exams=total_exams,
    total_examiners=total_examiners,total_students=total_students,
    total_slots=total_slots,total_bookings=total_bookings,
    courses=courses,exams=exams,pending_examiners=pending_examiners,
    search=search,found_users=found_users,found_exams=found_exams,found_bookings=found_bookings
    )

@app.route("/admin/users")
def admin_users():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    examiners = User.query.filter_by(role=Role.EXAMINER).all()
    students = User.query.filter_by(role=Role.STUDENT).all()

    return render_template("admin_users.html", examiners=examiners, students=students)

@app.route("/admin/examiner/add", methods=["GET", "POST"])
def add_examiner():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password")
        department = request.form.get("department", "").strip()
        designation = request.form.get("designation", "").strip()

        if not name or not email or not password or not department:
            flash("Name, email, password and department are required.", "danger")
            return redirect(url_for("add_examiner"))
        if not phone.isdigit() or len(phone) != 10:
            flash("Phone number must contain exactly 10 digits.", "danger")
            return redirect(url_for("add_examiner"))
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("add_examiner"))

        examiner = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
            role=Role.EXAMINER,
            approved=True,
            active=True
        )

        db.session.add(examiner)
        db.session.commit()

        profile = ExaminerProfile(user_id=examiner.id, department=department, designation=designation)
        db.session.add(profile)
        db.session.commit()

        flash("Examiner added successfully.", "success")

        return redirect(url_for("admin_users"))

    return render_template("examiner_form.html")

@app.route("/admin/approve/<int:user_id>", methods=["POST"])
def approve_examiner(user_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    if user.role == Role.EXAMINER:
        user.approved = True
        db.session.commit()
        flash("Examiner approved successfully.", "success")

    return redirect(request.referrer or url_for("admin_users"))

@app.route("/admin/deactivate/<int:user_id>", methods=["POST"])
def deactivate_user(user_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    if user.role != Role.ADMIN:
        user.active = False
        db.session.commit()
        flash("User deactivated successfully.", "success")

        if user.role == Role.EXAMINER and user.assigned_exams:
            flash("This examiner still has assigned examinations. Change the examiner from Edit Examination.", "warning")

    return redirect(url_for("admin_users"))

@app.route("/admin/activate/<int:user_id>", methods=["POST"])
def activate_user(user_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    if user.role != Role.ADMIN:
        user.active = True
        db.session.commit()
        flash("User activated successfully.", "success")

    return redirect(url_for("admin_users"))

def update_slot_status(slot):
    if slot.status in [SlotStatus.CANCELLED, SlotStatus.COMPLETED]:
        return
    if slot.available_seats == 0:
        slot.status = SlotStatus.FULL
    else:
        slot.status = SlotStatus.AVAILABLE

@app.route("/admin/slots")
def admin_slots():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    slots = ExamSlot.query.order_by(ExamSlot.slot_date).all()

    return render_template("admin_slots.html", slots=slots, examiners=active_examiners())

@app.route("/admin/slot/<int:slot_id>/change_examiner", methods=["POST"])
def change_slot_examiner(slot_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    slot = ExamSlot.query.get_or_404(slot_id)

    examiner = User.query.get(request.form.get("examiner_id"))

    if examiner is None or examiner.role != Role.EXAMINER or not examiner.approved or not examiner.active:
        flash("Please select a valid examiner.", "danger")
        return redirect(url_for("admin_slots"))

    slot.examiner_id = examiner.id
    db.session.commit()

    flash("Slot examiner changed to " + examiner.name + ".", "success")

    return redirect(url_for("admin_slots"))

@app.route("/admin/bookings")
def admin_bookings():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()

    return render_template("admin_bookings.html", bookings=bookings, BookingStatus=BookingStatus)

@app.route("/admin/booking/<int:booking_id>/reschedule", methods=["GET", "POST"])
def reschedule_booking(booking_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    booking = Booking.query.get_or_404(booking_id)

    if booking.status != BookingStatus.BOOKED:
        flash("Only active bookings can be rescheduled.", "warning")
        return redirect(url_for("admin_bookings"))

    free_slots = ExamSlot.query.filter(
        ExamSlot.exam_id == booking.exam_id,
        ExamSlot.id != booking.slot_id,
        ExamSlot.status == SlotStatus.AVAILABLE,
        ExamSlot.available_seats > 0
    ).all()

    if request.method == "POST":

        new_slot = ExamSlot.query.get(request.form.get("slot_id"))

        if new_slot is None or new_slot not in free_slots:
            flash("Please select a valid slot.", "danger")
            return redirect(url_for("reschedule_booking", booking_id=booking.id))

        old_slot = booking.slot

        old_slot.available_seats += 1
        new_slot.available_seats -= 1
        update_slot_status(old_slot)
        update_slot_status(new_slot)

        booking.slot_id = new_slot.id

        db.session.commit()

        flash("Booking rescheduled successfully.", "success")

        return redirect(url_for("admin_bookings"))

    return render_template("reschedule.html", booking=booking, free_slots=free_slots)

def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

@app.route("/admin/course/create", methods=["GET", "POST"])
def create_course():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":

        course_code = request.form.get("course_code", "").strip().upper()
        course_name = request.form.get("course_name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status")

        if not course_code or not course_name:
            flash("Course code and name are required.", "danger")
            return redirect(url_for("create_course"))

        if len(course_code) > 20:
            flash("Course code must be at most 20 characters.", "danger")
            return redirect(url_for("create_course"))

        if status not in CourseStatus.__members__:
            flash("Invalid course status.", "danger")
            return redirect(url_for("create_course"))

        if Course.query.filter_by(course_code=course_code).first():
            flash("Course code already exists.", "danger")
            return redirect(url_for("create_course"))

        course = Course(
            course_code=course_code,
            course_name=course_name,
            description=description,
            status=CourseStatus[status]
        )

        db.session.add(course)
        db.session.commit()

        flash("Course created successfully.", "success")

        return redirect(url_for("admin_dashboard"))

    return render_template("course_form.html", CourseStatus=CourseStatus)

@app.route("/admin/course/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    course = Course.query.get_or_404(course_id)

    if request.method == "POST":

        course_code = request.form.get("course_code", "").strip().upper()
        course_name = request.form.get("course_name", "").strip()

        if not course_code or not course_name:
            flash("Course code and name are required.", "danger")
            return redirect(url_for("edit_course", course_id=course.id))

        if len(course_code) > 20:
            flash("Course code must be at most 20 characters.", "danger")
            return redirect(url_for("edit_course", course_id=course.id))

        if request.form.get("status") not in CourseStatus.__members__:
            flash("Invalid course status.", "danger")
            return redirect(url_for("edit_course", course_id=course.id))

        existing = Course.query.filter_by(course_code=course_code).first()
        if existing and existing.id != course.id:
            flash("Course code already exists.", "danger")
            return redirect(url_for("edit_course", course_id=course.id))

        course.course_code = course_code
        course.course_name = course_name
        course.description = request.form.get("description", "").strip()
        course.status = CourseStatus[request.form.get("status")]

        db.session.commit()

        flash("Course updated successfully.", "success")

        return redirect(url_for("admin_dashboard"))

    return render_template("course_form.html", course=course, CourseStatus=CourseStatus)

@app.route("/admin/course/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    course = Course.query.get_or_404(course_id)

    if any(e.bookings for e in course.examinations):
        flash("This course has bookings. Set it to Inactive instead.", "danger")
        return redirect(url_for("admin_dashboard"))

    db.session.delete(course)
    db.session.commit()

    flash("Course deleted successfully.", "success")

    return redirect(url_for("admin_dashboard"))

def read_exam_form():

    data = {}
    data["course_id"] = request.form.get("course_id")
    data["exam_name"] = request.form.get("exam_name", "").strip()
    data["exam_type"] = request.form.get("exam_type")
    data["slot_creation_start"] = parse_date(request.form.get("slot_creation_start"))
    data["slot_creation_end"] = parse_date(request.form.get("slot_creation_end"))
    data["booking_start"] = parse_date(request.form.get("booking_start"))
    data["booking_end"] = parse_date(request.form.get("booking_end"))
    examiner_id = request.form.get("examiner_id")

    if not data["exam_name"]:
        return data, "Examination name is required."

    if Course.query.get(data["course_id"]) is None:
        return data, "Please select a valid course."

    if data["exam_type"] not in ExamType.__members__:
        return data, "Please select a valid examination type."

    try:
        data["duration_minutes"] = int(request.form.get("duration_minutes"))
        data["max_marks"] = int(request.form.get("max_marks"))
    except (ValueError, TypeError):
        return data, "Duration and maximum marks must be numbers."

    if data["duration_minutes"] <= 0 or data["max_marks"] <= 0:
        return data, "Duration and maximum marks must be greater than 0."

    if None in [data["slot_creation_start"], data["slot_creation_end"], data["booking_start"], data["booking_end"]]:
        return data, "All timeline dates are required."

    if data["slot_creation_end"] < data["slot_creation_start"]:
        return data, "Slot creation end cannot be before slot creation start."

    if data["booking_start"] < data["slot_creation_end"]:
        return data, "Booking can start only after slot creation ends."

    if data["booking_end"] < data["booking_start"]:
        return data, "Booking end cannot be before booking start."

    if examiner_id:
        examiner = User.query.get(examiner_id)
        if examiner is None or examiner.role != Role.EXAMINER or not examiner.approved or not examiner.active:
            return data, "Please select a valid examiner."
        data["examiner_id"] = examiner.id
    else:
        data["examiner_id"] = None

    return data, None

def active_examiners():
    return User.query.filter_by(role=Role.EXAMINER, approved=True, active=True).all()

@app.route("/admin/exam/create", methods=["GET", "POST"])
def create_exam():
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":

        data, error = read_exam_form()

        if error:
            flash(error, "danger")
            return redirect(url_for("create_exam"))

        if data["slot_creation_start"] < date.today():
            flash("Slot creation start cannot be in the past.", "danger")
            return redirect(url_for("create_exam"))

        exam = Examination(
            course_id=data["course_id"],
            exam_name=data["exam_name"],
            exam_type=ExamType[data["exam_type"]],
            duration_minutes=data["duration_minutes"],
            max_marks=data["max_marks"],
            slot_creation_start=data["slot_creation_start"],
            slot_creation_end=data["slot_creation_end"],
            booking_start=data["booking_start"],
            booking_end=data["booking_end"],
            examiner_id=data["examiner_id"],
            status=ExamStatus.DRAFT
        )

        db.session.add(exam)
        db.session.commit()

        flash("Examination created successfully.", "success")

        return redirect(url_for("exam_detail", exam_id=exam.id))

    courses = Course.query.filter_by(status=CourseStatus.ACTIVE).all()

    return render_template(
        "exam_form.html",
        courses=courses,
        examiners=active_examiners(),
        ExamType=ExamType,
        today=date.today().isoformat()
    )

@app.route("/admin/exam/edit/<int:exam_id>", methods=["GET", "POST"])
def edit_exam(exam_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    exam = Examination.query.get_or_404(exam_id)

    if request.method == "POST":

        data, error = read_exam_form()

        if error:
            flash(error, "danger")
            return redirect(url_for("edit_exam", exam_id=exam.id))

        exam.course_id = data["course_id"]
        exam.exam_name = data["exam_name"]
        exam.exam_type = ExamType[data["exam_type"]]
        exam.duration_minutes = data["duration_minutes"]
        exam.max_marks = data["max_marks"]
        exam.slot_creation_start = data["slot_creation_start"]
        exam.slot_creation_end = data["slot_creation_end"]
        exam.booking_start = data["booking_start"]
        exam.booking_end = data["booking_end"]
        exam.examiner_id = data["examiner_id"]

        if exam.examiner_id is not None:
            for slot in exam.slots:
                slot.examiner_id = exam.examiner_id

        db.session.commit()

        flash("Examination updated successfully.", "success")

        return redirect(url_for("exam_detail", exam_id=exam.id))

    courses = Course.query.all()

    return render_template(
        "exam_form.html",
        exam=exam,
        courses=courses,
        examiners=active_examiners(),
        ExamType=ExamType,
        today=date.today().isoformat()
    )

@app.route("/admin/exam/delete/<int:exam_id>", methods=["POST"])
def delete_exam(exam_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    exam = Examination.query.get_or_404(exam_id)

    if exam.bookings:
        flash("This examination has bookings. It cannot be deleted.", "danger")
        return redirect(url_for("admin_dashboard"))

    db.session.delete(exam)
    db.session.commit()

    flash("Examination deleted successfully.", "success")

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/exam/<int:exam_id>")
def exam_detail(exam_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    exam = Examination.query.get_or_404(exam_id)

    rubric_total = sum(r.max_marks for r in exam.rubrics)

    return render_template(
        "exam_detail.html",
        exam=exam,
        rubric_total=rubric_total,
        ExamStatus=ExamStatus
    )

@app.route("/admin/exam/<int:exam_id>/status", methods=["POST"])
def update_exam_status(exam_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    exam = Examination.query.get_or_404(exam_id)

    new_status = request.form.get("status")

    if new_status not in ExamStatus.__members__:
        flash("Invalid status.", "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    if new_status == "SLOT_CREATION" and exam.examiner_id is None:
        flash("Assign an examiner before opening slot creation.", "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    if exam.status == ExamStatus.COMPLETED and new_status != "COMPLETED":
        flash("A completed examination cannot be reopened.", "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    if new_status in ["DRAFT", "SLOT_CREATION"] and exam.bookings:
        flash("Students have already booked. The examination cannot go back to " + ExamStatus[new_status].value + ".", "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    if new_status == "BOOKING_OPEN" and len(exam.slots) == 0:
        flash("No slots created yet. Students would have nothing to book.", "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    if new_status == "BOOKING_OPEN" and len(exam.rubrics) == 0:
        flash("Add rubrics before opening booking, otherwise students cannot be evaluated.", "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    exam.status = ExamStatus[new_status]

    if exam.status == ExamStatus.COMPLETED:

        for booking in exam.bookings:
            if booking.status == BookingStatus.BOOKED:
                booking.status = BookingStatus.COMPLETED

        for slot in exam.slots:
            if slot.status != SlotStatus.CANCELLED:
                slot.status = SlotStatus.COMPLETED

    db.session.commit()

    flash("Examination status updated to " + exam.status.value + ".", "success")

    return redirect(url_for("exam_detail", exam_id=exam.id))

def read_rubric_form(exam, rubric=None):

    data = {}
    data["criterion_name"] = request.form.get("criterion_name", "").strip()
    data["description"] = request.form.get("description", "").strip()

    if not data["criterion_name"]:
        return data, "Criterion name is required."

    try:
        data["max_marks"] = int(request.form.get("max_marks"))
        data["weightage"] = float(request.form.get("weightage"))
    except (ValueError, TypeError):
        return data, "Maximum marks and weightage must be numbers."

    if data["max_marks"] <= 0 or data["weightage"] <= 0:
        return data, "Maximum marks and weightage must be greater than 0."

    other_total = sum(r.max_marks for r in exam.rubrics if r != rubric)
    if other_total + data["max_marks"] > exam.max_marks:
        return data, "Total rubric marks cannot exceed examination maximum marks (" + str(exam.max_marks) + ")."

    other_weight = sum(r.weightage for r in exam.rubrics if r != rubric)
    if other_weight + data["weightage"] > 100:
        return data, "Total weightage cannot exceed 100."

    return data, None

@app.route("/admin/exam/<int:exam_id>/rubric/add", methods=["POST"])
def add_rubric(exam_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    exam = Examination.query.get_or_404(exam_id)

    data, error = read_rubric_form(exam)

    if error:
        flash(error, "danger")
        return redirect(url_for("exam_detail", exam_id=exam.id))

    rubric = Rubric(
        exam_id=exam.id,
        criterion_name=data["criterion_name"],
        max_marks=data["max_marks"],
        weightage=data["weightage"],
        description=data["description"]
    )

    db.session.add(rubric)
    db.session.commit()

    flash("Rubric added successfully.", "success")

    return redirect(url_for("exam_detail", exam_id=exam.id))

@app.route("/admin/rubric/edit/<int:rubric_id>", methods=["GET", "POST"])
def edit_rubric(rubric_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    rubric = Rubric.query.get_or_404(rubric_id)
    exam = rubric.examination

    if request.method == "POST":

        data, error = read_rubric_form(exam, rubric)

        if error:
            flash(error, "danger")
            return redirect(url_for("edit_rubric", rubric_id=rubric.id))

        rubric.criterion_name = data["criterion_name"]
        rubric.max_marks = data["max_marks"]
        rubric.weightage = data["weightage"]
        rubric.description = data["description"]

        db.session.commit()

        flash("Rubric updated successfully.", "success")

        return redirect(url_for("exam_detail", exam_id=exam.id))

    return render_template("rubric_form.html", rubric=rubric, exam=exam)

@app.route("/admin/rubric/delete/<int:rubric_id>", methods=["POST"])
def delete_rubric(rubric_id):
    if session.get("role") != "ADMIN":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    rubric = Rubric.query.get_or_404(rubric_id)
    exam_id = rubric.exam_id

    if Evaluation.query.filter_by(rubric_id=rubric.id).first():
        flash("This rubric is already used in evaluations and cannot be deleted.", "danger")
        return redirect(url_for("exam_detail", exam_id=exam_id))

    db.session.delete(rubric)
    db.session.commit()

    flash("Rubric deleted successfully.", "success")

    return redirect(url_for("exam_detail", exam_id=exam_id))

@app.route("/examiner/dashboard")
def examiner_dashboard():
    if session.get("role") != "EXAMINER":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    examiner = User.query.get_or_404(session.get("user_id"))

    return render_template("examiner_dash.html", examiner=examiner)

@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "STUDENT":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    student = User.query.get_or_404(session.get("user_id"))

    return render_template("student_dash.html", student=student)

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)
