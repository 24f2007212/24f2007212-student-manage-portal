# Examination Management Portal

A Flask-based web application for managing examinations, examiners, students, examination slots and bookings.

## Features
- Admin, Examiner and Student roles with role-based access
- Student and examiner registration and login (examiners need admin approval)
- Admin dashboard with total counts and search by name or ID
- Course, examination and rubric management
- Examination timelines and status (open and close slot creation and booking)
- Add, approve, deactivate and activate examiners and students
- View all slots and bookings, reschedule bookings, change examiner
- Examiner dashboard with assigned exams, slots, booked students and pending evaluations
- Slot creation during the slot creation period, edit or remove before booking starts
- Rubric-based evaluation with marks and remarks
- Student dashboard with search and filter of available examinations
- Slot booking and cancellation before the booking deadline
- Duplicate booking and overbooking prevention, slot closes automatically when full
- Booking history, upcoming examinations and published results
- Admin result publishing
- Examination completion details and full booking records for admin

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

## Issues and Resolutions
- Students could open admin or examiner pages by typing the URL. Fixed by checking `session["role"]` at the start of every route.
- Same student could book the same exam twice. Fixed with a unique constraint on (student_id, exam_id) and a check before booking.
- A cancelled student could not book again because of the unique constraint. Fixed by reusing the cancelled booking row with the new slot.
- Slots could be overbooked. Fixed by checking `available_seats` before booking and marking the slot FULL when seats reach 0.
- Deleting a course or exam removed its booking history. Fixed by blocking the delete when bookings exist (the course can be set to Inactive instead).
- Examiner could create two slots at the same time. Fixed with a time clash check on the same date.
- Students could cancel after admin closed booking. Fixed by allowing cancel only when booking is open.
- A deactivated user who was already logged in could keep browsing. Fixed with a `before_request` check that clears the session.
- Total rubric weightage could go above 100. Fixed with a check when adding or editing a rubric.
- Changing an examination's examiner left its slots with the old examiner. Fixed by moving the slots to the new examiner too.
- An examination could be moved back to Draft after students booked. Fixed with status checks.
