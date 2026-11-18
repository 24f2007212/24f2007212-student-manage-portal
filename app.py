from flask import Flask,render_template,request,redirect,url_for,flash,session
from models import db,User,Role,ExaminerProfile,Course,Examination,Rubric,ExamSlot,Booking,Evaluation
from models import CourseStatus,ExamType,ExamStatus,SlotStatus,BookingStatus
import os
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime, date

app = Flask(__name__)
#configs
app.config["SECRET_KEY"] = "exam-management-portal"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "instance", "exam_portal.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)#connect

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
        approved=False if role == "EXAMINER" else True,#examiner needs admin approval
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

    return render_template("admin_dash.html")

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
