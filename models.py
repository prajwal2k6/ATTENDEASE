from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Association table for Student-Parent relationship
student_parent = db.Table('student_parent',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('parent_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher', 'student', 'parent'
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    marks = db.relationship('Mark', backref='student', lazy=True)
    projects = db.relationship('Project', backref='student', lazy=True)
    
    # For Parent-Student relationship
    # If this user is a parent, 'children' gives list of students
    # If this user is a student, 'parents' gives list of parents
    children = db.relationship('User', 
                               secondary=student_parent,
                               primaryjoin=(id == student_parent.c.parent_id),
                               secondaryjoin=(id == student_parent.c.student_id),
                               backref=db.backref('parents', lazy=True),
                               lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)  # 'Present', 'Absent'

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    test_name = db.Column(db.String(100), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Assigned') # Assigned, In Progress, Submitted, Graded
    grade = db.Column(db.String(10), nullable=True)

class TeacherRemark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Teacher ID
    remark = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

class Extracurricular(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    achievement_type = db.Column(db.String(50), nullable=False) # Sports, Cultural, Academic, etc.
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False) # UUID
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Present')

