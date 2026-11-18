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

db.init_app(app)#connect flask and sqlalchemy

#admin is created by code, no admin registration
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)
