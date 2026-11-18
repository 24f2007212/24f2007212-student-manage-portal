# Examination Management Portal

A Flask-based web application for managing examinations, examiners, students, examination slots and bookings.

## Features
- Admin, Examiner and Student roles
- User registration and login
- Role-based access control
- Course and examination management
- Examination rubrics
- Examiner approval and deactivation
- Examination slot creation and booking
- Booking cancellation and duplicate booking prevention
- Evaluation with marks and remarks
- Result publishing and booking history

## Database
The application uses SQLite with these tables:
- User
- ExaminerProfile
- Course
- Examination
- Rubric
- ExamSlot
- Booking
- Evaluation

The ER diagram is available in the `db diagram/` folder.

## How to Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Admin login: admin@exam.com / admin123
