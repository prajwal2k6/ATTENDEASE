from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Attendance, Activity, Mark, Project, TeacherRemark, Extracurricular, AttendanceSession, AttendanceRecord
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hackathon-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sih.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.jinja_env.globals.update(now=datetime.utcnow)

@app.route('/')
def index():
    # Home page should be accessible to everyone, logged in or not
    # No auto-redirects
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            
            # Redirect to Home Page instead of Dashboard
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Teacher Dashboard
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    # Get all students
    students = User.query.filter_by(role='student').all()
    
    # Get recent activities
    activities = Activity.query.order_by(Activity.date.desc()).limit(5).all()
    
    # Date string for the form default
    date_string = datetime.utcnow().strftime('%Y-%m-%d')
    
    return render_template('teacher_dashboard.html', students=students, activities=activities, date_string=date_string)

@app.route('/teacher/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    date_str = request.form.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    students = User.query.filter_by(role='student').all()
    for student in students:
        status = request.form.get(f'status_{student.id}')
        if status:
            # Check if record exists
            existing = Attendance.query.filter_by(student_id=student.id, date=date_obj).first()
            if existing:
                existing.status = status
            else:
                new_record = Attendance(student_id=student.id, date=date_obj, status=status)
                db.session.add(new_record)
    
    db.session.commit()
    flash('Attendance marked successfully!')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/add_activity', methods=['POST'])
def add_activity():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    description = request.form.get('description')
    date_str = request.form.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    new_activity = Activity(
        title=title,
        description=description,
        date=date_obj,
        assigned_by=session['user_id']
    )
    db.session.add(new_activity)
    db.session.commit()
    flash('Activity added successfully!')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/students')
def student_list():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    students = User.query.filter_by(role='student').all()
    return render_template('students_list.html', students=students)

@app.route('/teacher/student/<int:student_id>')
def student_profile(student_id):
    if 'user_id' not in session or session.get('role') not in ['teacher', 'parent']:
         # Parents can also view, but with restrictions (handled in template or check here)
         # For strict security: if parent, check if student is their child
         if session.get('role') == 'parent':
             parent = User.query.get(session['user_id'])
             student = User.query.get(student_id)
             if student not in parent.children:
                 return redirect(url_for('parent_dashboard'))
         elif session.get('role') != 'teacher':
            return redirect(url_for('login'))
    
    student = User.query.get_or_404(student_id)
    
    # Calculate Attendance
    total_days = Attendance.query.filter_by(student_id=student.id).count()
    present_days = Attendance.query.filter_by(student_id=student.id, status='Present').count()
    attendance_percentage = 0
    if total_days > 0:
        attendance_percentage = round((present_days / total_days) * 100, 2)
        
    marks = Mark.query.filter_by(student_id=student.id).all()
    projects = Project.query.filter_by(student_id=student.id).all()
    remarks = TeacherRemark.query.filter_by(student_id=student.id).order_by(TeacherRemark.date.desc()).all()
    extracurriculars = Extracurricular.query.filter_by(student_id=student.id).order_by(Extracurricular.date.desc()).all()
    
    return render_template('student_profile.html', student=student, 
                           attendance_percentage=attendance_percentage,
                           marks=marks, projects=projects, remarks=remarks, extracurriculars=extracurriculars)

@app.route('/teacher/mark/add/<int:student_id>', methods=['POST'])
def add_mark(student_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    subject = request.form.get('subject')
    test_name = request.form.get('test_name')
    marks_obtained = float(request.form.get('marks_obtained'))
    max_marks = float(request.form.get('max_marks'))
    
    new_mark = Mark(student_id=student_id, subject=subject, test_name=test_name,
                    marks_obtained=marks_obtained, max_marks=max_marks)
    db.session.add(new_mark)
    db.session.commit()
    flash('Marks added successfully!')
    return redirect(url_for('student_profile', student_id=student_id))

@app.route('/teacher/project/add/<int:student_id>', methods=['POST'])
def add_project(student_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    description = request.form.get('description')
    
    new_project = Project(student_id=student_id, title=title, description=description)
    db.session.add(new_project)
    db.session.commit()
    flash('Project assigned successfully!')
    return redirect(url_for('student_profile', student_id=student_id))

@app.route('/teacher/project/update/<int:project_id>', methods=['POST'])
def update_project(project_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    project = Project.query.get_or_404(project_id)
    project.status = request.form.get('status')
    project.grade = request.form.get('grade')
    
    db.session.commit()
    flash('Project updated successfully!')
    return redirect(url_for('student_profile', student_id=project.student_id))

@app.route('/teacher/remark/add/<int:student_id>', methods=['POST'])
def add_remark(student_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    remark_text = request.form.get('remark')
    
    new_remark = TeacherRemark(student_id=student_id, assigned_by=session['user_id'], remark=remark_text)
    db.session.add(new_remark)
    db.session.commit()
    flash('Remark added successfully!')
    return redirect(url_for('student_profile', student_id=student_id))

@app.route('/teacher/extracurricular/add/<int:student_id>', methods=['POST'])
def add_extracurricular(student_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    description = request.form.get('description')
    achievement_type = request.form.get('achievement_type')
    
    new_achievement = Extracurricular(student_id=student_id, title=title, description=description, achievement_type=achievement_type)
    db.session.add(new_achievement)
    db.session.commit()
    flash('Extracurricular achievement added successfully!')
    return redirect(url_for('student_profile', student_id=student_id))

# QR Attendance Routes
@app.route('/teacher/attendance/generate')
def generate_qr_page():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    # Check for existing active session
    active_session = AttendanceSession.query.filter_by(teacher_id=session['user_id'], is_active=True).first()
    
    current_session = None
    if active_session:
        # Check if it's already expired by time, even if marked active
        if datetime.utcnow() > active_session.expires_at:
            active_session.is_active = False
            db.session.commit()
        else:
            current_session = {
                'session_id': active_session.session_id,
                'expires_at': active_session.expires_at.isoformat()
            }
            
    return render_template('generate_qr.html', active_session=current_session)

@app.route('/api/qr/generate', methods=['POST'])
def generate_qr_api():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Invalidate previous active sessions for this teacher
    active_sessions = AttendanceSession.query.filter_by(teacher_id=session['user_id'], is_active=True).all()
    for s in active_sessions:
        s.is_active = False
    
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=3)
    
    new_session = AttendanceSession(
        session_id=session_id,
        teacher_id=session['user_id'],
        expires_at=expires_at,
        is_active=True
    )
    
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({'session_id': session_id, 'expires_at': expires_at.isoformat()})

@app.route('/student/attendance/scan')
def scan_qr_page():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    return render_template('scan_qr.html')

@app.route('/api/qr/scan', methods=['POST'])
def scan_qr_api():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Invalid QR Code'}), 400
        
    # validate session
    qr_session = AttendanceSession.query.filter_by(session_id=session_id).first()
    
    if not qr_session:
        return jsonify({'error': 'Invalid Session'}), 404
        
    if not qr_session.is_active:
        return jsonify({'error': 'Session Expired (Inactive)'}), 400
        
    if datetime.utcnow() > qr_session.expires_at:
        qr_session.is_active = False # Mark as inactive
        db.session.commit()
        return jsonify({'error': 'Session Expired (Timeout)'}), 400
        
    # Check if already marked for this session
    existing_record = AttendanceRecord.query.filter_by(student_id=session['user_id'], session_id=qr_session.id).first()
    if existing_record:
        return jsonify({'message': 'Attendance already marked for this session.'}), 200
        
    # Mark Attendance
    new_record = AttendanceRecord(
        student_id=session['user_id'],
        session_id=qr_session.id,
        status='Present'
    )
    db.session.add(new_record)
    
    # Also mark daily attendance if not present
    today = datetime.utcnow().date()
    daily_att = Attendance.query.filter_by(student_id=session['user_id'], date=today).first()
    if not daily_att:
        daily_att = Attendance(student_id=session['user_id'], date=today, status='Present')
        db.session.add(daily_att)
    elif daily_att.status != 'Present':
        daily_att.status = 'Present'
        
    db.session.commit()
    
    return jsonify({'message': 'Attendance Marked Successfully!'}), 200


# Student Dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    
    # Calculate Attendance Percentage
    total_days = Attendance.query.filter_by(student_id=user_id).count()
    present_days = Attendance.query.filter_by(student_id=user_id, status='Present').count()
    attendance_percentage = 0
    if total_days > 0:
        attendance_percentage = round((present_days / total_days) * 100, 2)

    # Simplified Dashboard Data (Counts Only)
    marks_count = Mark.query.filter_by(student_id=user_id).count()
    projects_count = Project.query.filter_by(student_id=user_id).count()
    extracurriculars_count = Extracurricular.query.filter_by(student_id=user_id).count()
    
    return render_template('student_dashboard.html', 
                           attendance_percentage=attendance_percentage,
                           marks_count=marks_count,
                           projects_count=projects_count,
                           extracurriculars_count=extracurriculars_count)

@app.route('/student/attendance')
def student_attendance():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    attendance_history = Attendance.query.filter_by(student_id=user_id).order_by(Attendance.date.desc()).all()
    
    return render_template('student_attendance.html', attendance_history=attendance_history)

@app.route('/student/results')
def student_results():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    marks = Mark.query.filter_by(student_id=user_id).all()
    
    return render_template('student_results.html', marks=marks)

@app.route('/student/projects')
def student_projects():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    projects = Project.query.filter_by(student_id=user_id).all()
    
    return render_template('student_projects.html', projects=projects)

@app.route('/student/remarks')
def student_remarks():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    remarks = TeacherRemark.query.filter_by(student_id=user_id).order_by(TeacherRemark.date.desc()).all()
    
    return render_template('student_remarks.html', remarks=remarks)

@app.route('/student/achievements')
def student_achievements():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    extracurriculars = Extracurricular.query.filter_by(student_id=user_id).order_by(Extracurricular.date.desc()).all()
    
    return render_template('student_achievements.html', extracurriculars=extracurriculars)

# Parent Dashboard
@app.route('/parent/dashboard')
def parent_dashboard():
    if 'user_id' not in session or session.get('role') != 'parent':
        return redirect(url_for('login'))
    
    parent_id = session['user_id']
    parent = User.query.get(parent_id)
    children = parent.children
    
    return render_template('parent_dashboard.html', children=children)

# Initialize DB command
@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.create_all()
        
        # Seed Data if empty
        if not User.query.first():
            print("Seeding database...")
            # Create a Teacher
            teacher = User(
                name="Amit Sharma",
                email="teacher@school.com",
                password=generate_password_hash("password123"),
                role="teacher"
            )
            # Create Students
            student1 = User(
                name="Riya Patel",
                email="riya@student.com",
                password=generate_password_hash("password123"),
                role="student"
            )
            student2 = User(
                name="Arjun Singh",
                email="arjun@student.com",
                password=generate_password_hash("password123"),
                role="student"
            )
            
            # Create Parent
            parent1 = User(
                name="Suresh Patel",
                email="parent@school.com",
                password=generate_password_hash("password123"),
                role="parent"
            )
            
            # Create Deme Students
            student3 = User(
                name="Vikram Malhotra",
                email="vikram@student.com",
                password=generate_password_hash("password123"),
                role="student"
            )
            student4 = User(
                name="Ananya Iyer",
                email="ananya@student.com",
                password=generate_password_hash("password123"),
                role="student"
            )
            student5 = User(
                name="Rohan Das",
                email="rohan@student.com",
                password=generate_password_hash("password123"),
                role="student"
            )
            
            db.session.add(teacher)
            db.session.add(student1)
            db.session.add(student2)
            db.session.add(student3)
            db.session.add(student4)
            db.session.add(student5)
            db.session.add(parent1)
            db.session.commit()
            
            # Link Parent to Multiple Students
            parent1.children.append(student1)
            parent1.children.append(student3) # Example: Parent has two children
            db.session.commit()
            
            # Seed Additional Data
            
            # --- Student 1: Riya Patel ---
            # Attendance
            db.session.add(Attendance(student_id=student1.id, date=datetime(2025, 1, 10).date(), status='Present'))
            db.session.add(Attendance(student_id=student1.id, date=datetime(2025, 1, 11).date(), status='Present'))
            db.session.add(Attendance(student_id=student1.id, date=datetime(2025, 1, 12).date(), status='Absent'))
            # Marks
            db.session.add(Mark(student_id=student1.id, subject="Mathematics", test_name="Unit Test 1", marks_obtained=45, max_marks=50))
            db.session.add(Mark(student_id=student1.id, subject="Physics", test_name="Unit Test 1", marks_obtained=38, max_marks=50))
            db.session.add(Mark(student_id=student1.id, subject="Chemistry", test_name="Mid-Term", marks_obtained=85, max_marks=100))
            # Projects
            db.session.add(Project(student_id=student1.id, title="Solar System Model", description="Create a working model of the solar system.", status="In Progress"))
            db.session.add(Project(student_id=student1.id, title="History Essay", description="Essay on Indian Independence Movement.", status="Submitted", grade="B+"))
            # Remarks
            db.session.add(TeacherRemark(student_id=student1.id, assigned_by=teacher.id, remark="Riya needs to improve focus in Physics classes.", date=datetime.utcnow().date()))
            db.session.add(TeacherRemark(student_id=student1.id, assigned_by=teacher.id, remark="Great leadership shown in group activities.", date=datetime(2024, 12, 15).date()))
            # Extracurricular
            db.session.add(Extracurricular(student_id=student1.id, title="Inter-School Debate", description="Won 2nd prize in debate competition.", achievement_type="Cultural", date=datetime.utcnow().date()))

            # --- Student 2: Arjun Singh ---
            # Attendance
            db.session.add(Attendance(student_id=student2.id, date=datetime(2025, 1, 10).date(), status='Present'))
            db.session.add(Attendance(student_id=student2.id, date=datetime(2025, 1, 11).date(), status='Absent'))
            db.session.add(Attendance(student_id=student2.id, date=datetime(2025, 1, 12).date(), status='Present'))
            # Marks
            db.session.add(Mark(student_id=student2.id, subject="Mathematics", test_name="Unit Test 1", marks_obtained=40, max_marks=50))
            db.session.add(Mark(student_id=student2.id, subject="English", test_name="Mid-Term", marks_obtained=78, max_marks=100))
            # Projects
            db.session.add(Project(student_id=student2.id, title="Plant Growth Study", description="Observe and record plant growth over 4 weeks.", status="Completed", grade="A"))
            # Remarks
            db.session.add(TeacherRemark(student_id=student2.id, assigned_by=teacher.id, remark="Arjun is very attentive and participative.", date=datetime.utcnow().date()))
            # Extracurricular
            db.session.add(Extracurricular(student_id=student2.id, title="District Football Match", description="Man of the Match in district finals.", achievement_type="Sports", date=datetime(2024, 11, 20).date()))

            # --- Student 3: Vikram Malhotra ---
            # Attendance
            db.session.add(Attendance(student_id=student3.id, date=datetime(2025, 1, 10).date(), status='Present'))
            db.session.add(Attendance(student_id=student3.id, date=datetime(2025, 1, 11).date(), status='Present'))
            db.session.add(Attendance(student_id=student3.id, date=datetime(2025, 1, 12).date(), status='Present'))
            # Marks
            db.session.add(Mark(student_id=student3.id, subject="Computer Science", test_name="Mid-Term", marks_obtained=92, max_marks=100))
            db.session.add(Mark(student_id=student3.id, subject="Mathematics", test_name="Unit Test 1", marks_obtained=50, max_marks=50))
            # Projects
            db.session.add(Project(student_id=student3.id, title="AI Chatbot", description="Develop a simple chatbot using Python.", status="Submitted", grade="A+"))
            db.session.add(Project(student_id=student3.id, title="Robotics Arm", description="Build a hydraulic robotic arm.", status="In Progress"))
            # Remarks
            db.session.add(TeacherRemark(student_id=student3.id, assigned_by=teacher.id, remark="Excellent performance in coding and logic.", date=datetime.utcnow().date()))
            # Extracurricular
            db.session.add(Extracurricular(student_id=student3.id, title="Science Olympiad", description="Gold medalist in National Science Olympiad.", achievement_type="Academic", date=datetime(2024, 10, 5).date()))

            # --- Student 4: Ananya Iyer ---
            # Attendance
            db.session.add(Attendance(student_id=student4.id, date=datetime(2025, 1, 10).date(), status='Absent'))
            db.session.add(Attendance(student_id=student4.id, date=datetime(2025, 1, 11).date(), status='Present'))
            db.session.add(Attendance(student_id=student4.id, date=datetime(2025, 1, 12).date(), status='Present'))
            # Marks
            db.session.add(Mark(student_id=student4.id, subject="Literature", test_name="Unit Test 1", marks_obtained=48, max_marks=50))
            db.session.add(Mark(student_id=student4.id, subject="History", test_name="Mid-Term", marks_obtained=88, max_marks=100))
            # Projects
            db.session.add(Project(student_id=student4.id, title="Poetry Anthology", description="Compile a collection of self-written poems.", status="Completed", grade="A"))
            # Remarks
            db.session.add(TeacherRemark(student_id=student4.id, assigned_by=teacher.id, remark="Ananya shows great creative writing skills.", date=datetime.utcnow().date()))
            # Extracurricular
            db.session.add(Extracurricular(student_id=student4.id, title="Classical Dance Recital", description="Performed Bharatanatyam at Annual Day.", achievement_type="Cultural", date=datetime(2024, 12, 20).date()))

            # --- Student 5: Rohan Das ---
            # Attendance
            db.session.add(Attendance(student_id=student5.id, date=datetime(2025, 1, 10).date(), status='Present'))
            db.session.add(Attendance(student_id=student5.id, date=datetime(2025, 1, 11).date(), status='Present'))
            # Marks
            db.session.add(Mark(student_id=student5.id, subject="Biology", test_name="Unit Test 1", marks_obtained=35, max_marks=50))
            db.session.add(Mark(student_id=student5.id, subject="Physics", test_name="Unit Test 1", marks_obtained=40, max_marks=50))
            # Projects
            db.session.add(Project(student_id=student5.id, title="Water Purification System", description="Design a low-cost water filter.", status="Assigned"))
            # Remarks
            db.session.add(TeacherRemark(student_id=student5.id, assigned_by=teacher.id, remark="Rohan needs to be more punctual with submissions.", date=datetime.utcnow().date()))
            # Extracurricular
            db.session.add(Extracurricular(student_id=student5.id, title="Inter-House Cricket", description="Captain of the winning team.", achievement_type="Sports", date=datetime(2024, 11, 15).date()))

            db.session.commit()
            
            print("Database seeded!")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    app.run(debug=True)
