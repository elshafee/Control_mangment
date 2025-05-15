from datetime import datetime
from enum import Enum

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'K!8d@Z%1qC'  # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use your database URI
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

subject_types = ["regular", "form", "drawing"]


class Role(Enum):
    ADMIN = 'admin'
    USER = 'user'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.ADMIN)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'))
    sector = db.relationship('Sector', backref=db.backref('users', lazy=True))
    controls = db.relationship('Control', secondary='control_authorized_user',
                               backref=db.backref('authorized_users', lazy=True))

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"


class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Sector('{self.name}')"


class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"Semester('{self.name}', '{self.start_date}', '{self.end_date}')"


class Control(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)

    def __repr__(self):
        return f"Control('{self.name}')"


control_authorized_user = db.Table('control_authorized_user',
                                   db.Column('control_id', db.Integer, db.ForeignKey('control.id'), primary_key=True),
                                   db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True))


class SubjectType(Enum):
    REGULAR = "regular"
    FORM = "form"
    DRAWING = "drawing"


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(SubjectType), nullable=False)
    exam_date = db.Column(db.Date)
    exam_day = db.Column(db.String(20))
    exam_time = db.Column(db.String(20))
    students_total = db.Column(db.Integer)
    present = db.Column(db.Integer)
    absent = db.Column(db.Integer)
    deprived = db.Column(db.Integer)
    withdrawn = db.Column(db.Integer)
    is_recorded = db.Column(db.Boolean, default=False)
    is_reviewed = db.Column(db.Boolean, default=False)
    is_final_reviewed = db.Column(db.Boolean, default=False)
    prepared = db.Column(db.Boolean, default=False)
    year_grade = db.Column(db.Boolean, default=False)
    answer_model = db.Column(db.Boolean, default=False)
    incomplete = db.Column(db.Integer, default=0)
    expulsion = db.Column(db.Integer, default=0)
    cheating_report = db.Column(db.Integer, default=0)
    misconduct_report = db.Column(db.Integer, default=0)
    grading = db.Column(db.Boolean, default=False)
    review = db.Column(db.Boolean, default=False)
    recording_grades = db.Column(db.Boolean, default=False)
    grade_entry_review = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    control_id = db.Column(db.Integer, db.ForeignKey('control.id'), nullable=False)

    def __repr__(self):
        return f"Subject('{self.code}', '{self.name}')"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)  # In real app, hash the password!
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # In real app, use password hashing!
            login_user(user)
            print(current_user.role)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    print(current_user)
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    semesters = Semester.query.all()
    return render_template('dashboard.html', semesters=semesters, Role=Role)


# --- Admin Routes ---
@app.route('/admin/sectors')
@login_required
def list_sectors_admin():
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    sectors = Sector.query.all()
    return render_template('admin/sector/list.html', sectors=sectors, Role=Role)


@app.route('/admin/sectors/add', methods=['GET', 'POST'])
@login_required
def add_sector_admin():
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        new_sector = Sector(name=name)
        db.session.add(new_sector)
        db.session.commit()
        flash(f"Sector '{name}' added successfully.", "success")
        return redirect(url_for('list_sectors_admin'))
    return render_template('admin/sector/add.html', Role=Role)


@app.route('/admin/sectors/edit/<int:sector_id>', methods=['GET', 'POST'])
@login_required
def edit_sector_admin(sector_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    sector = Sector.query.get_or_404(sector_id)
    if request.method == 'POST':
        sector.name = request.form['name']
        db.session.commit()
        flash(f"Sector '{sector.name}' updated successfully.", "success")
        return redirect(url_for('list_sectors_admin'))
    return render_template('admin/sector/edit.html', sector=sector, Role=Role)


@app.route('/admin/sectors/delete/<int:sector_id>')
@login_required
def delete_sector_admin(sector_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    sector = Sector.query.get_or_404(sector_id)
    db.session.delete(sector)
    db.session.commit()
    flash(f"Sector '{sector.name}' deleted successfully.", "success")
    return redirect(url_for('list_sectors_admin'))


@app.route('/admin/users')
@login_required
def list_users_admin():
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    users = User.query.all()
    sectors = Sector.query.all()
    return render_template('admin/user/list.html', users=users, sectors=sectors, Role=Role)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def add_user_admin():
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    sectors = Sector.query.all()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_str = request.form['role']
        sector_id = request.form.get('sector_id')  # Use get() to handle optional field

        role = Role(role_str)
        new_user = User(username=username, password=password, role=role,
                        sector_id=sector_id)  # Hash password in real app!
        db.session.add(new_user)
        db.session.commit()
        flash(f"User '{username}' added successfully.", "success")
        return redirect(url_for('list_users_admin'))
    return render_template('admin/user/add.html', sectors=sectors, Role=Role)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user_admin(user_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    sectors = Sector.query.all()
    controls = Control.query.all()
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:  # Only change password if a new one is provided
            user.password = request.form['password']  # Hash password in real app!
        user.role = Role(request.form['role'])
        user.sector_id = request.form.get('sector_id')

        # Handle allowed controls
        user.controls.clear()  # Remove existing associations
        selected_control_ids = request.form.getlist('controls')  # Get list of selected control IDs
        for control_id in selected_control_ids:
            control = Control.query.get(int(control_id))
            if control:
                user.controls.append(control)

        db.session.commit()
        flash(f"User '{user.username}' updated successfully.", "success")
        return redirect(url_for('list_users_admin'))
    return render_template('admin/user/edit.html', user=user, sectors=sectors, controls=controls, Role=Role)


@app.route('/semester')
@login_required
def list_semesters():
    semesters = Semester.query.all()
    return render_template('semester/list.html', semesters=semesters, Role=Role)


@app.route('/admin/users/delete/<int:user_id>')
@login_required
def delete_user_admin(user_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted successfully.", "success")
    return redirect(url_for('list_users_admin'))


# --- Semester CRUD Routes ---
@app.route('/semester/add', methods=['GET', 'POST'])
@login_required
def add_semester():
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to add semesters.", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        new_semester = Semester(name=name, start_date=start_date, end_date=end_date)
        db.session.add(new_semester)
        db.session.commit()
        flash(f"Semester '{name}' added successfully.", "success")
        return redirect(url_for('dashboard'))
    return render_template('semester/add.html', Role=Role)


@app.route('/semester/edit/<int:semester_id>', methods=['GET', 'POST'])
@login_required
def edit_semester(semester_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to edit semesters.", "danger")
        return redirect(url_for('dashboard'))
    semester = Semester.query.get_or_404(semester_id)
    if request.method == 'POST':
        semester.name = request.form['name']
        semester.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        semester.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        db.session.commit()
        flash(f"Semester '{semester.name}' updated successfully.", "success")
        return redirect(url_for('dashboard'))
    return render_template('semester/edit.html', semester=semester, Role=Role)


@app.route('/semester/delete/<int:semester_id>')
@login_required
def delete_semester(semester_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to delete semesters.", "danger")
        return redirect(url_for('dashboard'))
    semester = Semester.query.get_or_404(semester_id)
    db.session.delete(semester)
    db.session.commit()
    flash(f"Semester '{semester.name}' deleted successfully.", "success")
    return redirect(url_for('dashboard'))


# --- Control CRUD Routes ---
@app.route('/semester/<int:semester_id>/control')
@login_required
def list_control(semester_id):

    semester = Semester.query.get_or_404(semester_id)
    controls = Control.query.filter_by(semester_id=semester_id).all()
    return render_template('control/list.html', semester=semester, controls=controls, Role=Role)


@app.route('/semester/<int:semester_id>/control/add', methods=['GET', 'POST'])
@login_required
def add_control(semester_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to add controls.", "danger")
        return redirect(url_for('dashboard'))
    semester = Semester.query.get_or_404(semester_id)
    if request.method == 'POST':
        name = request.form['name']
        notes = request.form['notes']
        new_control = Control(name=name, notes=notes, semester_id=semester_id)
        db.session.add(new_control)
        db.session.commit()
        flash(f"Control '{name}' added successfully.", "success")
        return redirect(url_for('list_control', semester_id=semester_id))
    return render_template('control/add.html', semester=semester, Role=Role)


@app.route('/control/edit/<int:control_id>', methods=['GET', 'POST'])
@login_required
def edit_control(control_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to edit controls.", "danger")
        return redirect(url_for('dashboard'))
    control = Control.query.get_or_404(control_id)
    if request.method == 'POST':
        control.name = request.form['name']
        control.notes = request.form['notes']
        db.session.commit()
        flash(f"Control '{control.name}' updated successfully.", "success")
        return redirect(url_for('list_control', semester_id=control.semester_id))
    return render_template('control/edit.html', control=control, Role=Role)


@app.route('/control/delete/<int:control_id>')
@login_required
def delete_control(control_id):
    if current_user.role != Role.ADMIN:
        flash("You do not have permission to delete controls.", "danger")
        return redirect(url_for('dashboard'))
    control = Control.query.get_or_404(control_id)
    db.session.delete(control)
    db.session.commit()
    flash(f"Control '{control.name}' deleted successfully.", "success")
    return redirect(url_for('list_control', semester_id=control.semester_id))


# --- Subject CRUD Routes ---
@app.route('/control/<int:control_id>/subjects')
@login_required
def list_subjects(control_id):
    control = Control.query.get_or_404(control_id)
    subjects = Subject.query.filter_by(control_id=control_id).all()
    return render_template('subject/list.html', control=control, subjects=subjects, Role=Role)


@app.route('/control/<int:control_id>/subjects/add', methods=['GET', 'POST'])
@login_required
def add_subject(control_id):
    control = Control.query.get_or_404(control_id)
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        type_str = request.form['type']
        exam_date_str = request.form['exam_date']
        exam_day = request.form['exam_day']
        exam_time = request.form['exam_time']
        students_total = request.form['students_total']
        present = request.form['present']
        absent = request.form['absent']
        deprived = request.form['deprived']
        withdrawn = request.form['withdrawn']

        is_recorded = 'is_recorded' in request.form
        is_reviewed = 'is_reviewed' in request.form
        is_final_reviewed = 'is_final_reviewed' in request.form
        prepared = 'prepared' in request.form
        year_grade = 'year_grade' in request.form
        answer_model = 'answer_model' in request.form
        incomplete = request.form['incomplete']
        expulsion = request.form['expulsion']
        cheating_report = request.form['cheating_report']
        misconduct_report = request.form['misconduct_report']
        grading = 'grading' in request.form
        review = 'review' in request.form
        recording_grades = 'recording_grades' in request.form
        grade_entry_review = 'grade_entry_review' in request.form
        notes = request.form['notes']

        type = SubjectType(type_str)
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None

        new_subject = Subject(code=code, name=name, type=type, exam_date=exam_date, exam_day=exam_day,
                              exam_time=exam_time, students_total=students_total, present=present, absent=absent,
                              deprived=deprived, withdrawn=withdrawn, is_recorded=is_recorded, is_reviewed=is_reviewed,
                              is_final_reviewed=is_final_reviewed, prepared=prepared, year_grade=year_grade,
                              answer_model=answer_model, incomplete=incomplete, expulsion=expulsion,
                              cheating_report=cheating_report, misconduct_report=misconduct_report, grading=grading,
                              review=review, recording_grades=recording_grades, grade_entry_review=grade_entry_review,
                              notes=notes, control_id=control_id)

        db.session.add(new_subject)
        db.session.commit()
        flash(f"Subject '{name}' added successfully.", "success")
        return redirect(url_for('list_subjects', control_id=control_id))
    return render_template('subject/add.html', control=control, SubjectType=SubjectType, Role=Role)


@app.route('/subject/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    control = Control.query.get_or_404(subject.control_id)
    if request.method == 'POST':
        subject.code = request.form['code']
        subject.name = request.form['name']
        subject.type = SubjectType(request.form['type'])
        exam_date_str = request.form['exam_date']
        subject.exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None
        subject.exam_day = request.form['exam_day']
        subject.exam_time = request.form['exam_time']
        subject.students_total = request.form['students_total']
        subject.present = request.form['present']
        subject.absent = request.form['absent']
        subject.deprived = request.form['deprived']
        subject.withdrawn = request.form['withdrawn']
        subject.is_recorded = 'is_recorded' in request.form
        subject.is_reviewed = 'is_reviewed' in request.form
        subject.is_final_reviewed = 'is_final_reviewed' in request.form
        subject.prepared = 'prepared' in request.form
        subject.year_grade = 'year_grade' in request.form
        subject.answer_model = 'answer_model' in request.form
        subject.incomplete = request.form['incomplete']
        subject.expulsion = request.form['expulsion']
        subject.cheating_report = request.form['cheating_report']
        subject.misconduct_report = request.form['misconduct_report']
        subject.grading = 'grading' in request.form
        subject.review = 'review' in request.form
        subject.recording_grades = 'recording_grades' in request.form
        subject.grade_entry_review = 'grade_entry_review' in request.form
        subject.notes = request.form['notes']

        db.session.commit()
        flash(f"Subject '{subject.name}' updated successfully.", "success")
        return redirect(url_for('list_subjects', control_id=subject.control_id))
    return render_template('subject/edit.html', subject=subject, control=control, SubjectType=SubjectType, Role=Role)


@app.route('/subject/delete/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    control_id = subject.control_id
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' deleted successfully.", "success")
    return redirect(url_for('list_subjects', control_id=control_id))


@app.route('/control/<int:control_id>/subjects/update', methods=['POST'])
@login_required
def update_subject(control_id):
    control = Control.query.get_or_404(control_id)
    subjects = Subject.query.filter_by(control_id=control_id).all()

    for subject in subjects:
        prepared_key = f'prepared_{subject.id}'
        year_grade_key = f'year_grade_{subject.id}'
        answer_model_key = f'answer_model_{subject.id}'
        incomplete_key = f'incomplete_{subject.id}'
        withdrawn_key = f'withdrawn_{subject.id}'
        absent_key = f'absent_{subject.id}'
        attendees_key = f'attendees_{subject.id}'
        expulsion_key = f'expulsion_{subject.id}'
        cheating_report_key = f'cheating_report_{subject.id}'
        misconduct_report_key = f'misconduct_report_{subject.id}'
        grading_key = f'grading_{subject.id}'
        review_key = f'review_{subject.id}'
        recording_grades_key = f'recording_grades_{subject.id}'
        grade_entry_review_key = f'grade_entry_review_{subject.id}'
        notes_key = f'notes_{subject.id}'

        if prepared_key in request.form:
            subject.prepared = True
        else:
            subject.prepared = False

        if year_grade_key in request.form:
            subject.year_grade = True
        else:
            subject.year_grade = False

        if answer_model_key in request.form:
            subject.answer_model = True
        else:
            subject.answer_model = False

        subject.incomplete = request.form.get(incomplete_key, type=int, default=0)
        subject.withdrawn = request.form.get(withdrawn_key, type=int, default=0)
        subject.absent = request.form.get(absent_key, type=int, default=0)
        subject.present = request.form.get(attendees_key, type=int, default=0)
        subject.expulsion = request.form.get(expulsion_key, type=int, default=0)
        subject.cheating_report = request.form.get(cheating_report_key, type=int, default=0)
        subject.misconduct_report = request.form.get(misconduct_report_key, type=int, default=0)

        if grading_key in request.form:
            subject.grading = True
        else:
            subject.grading = False

        if review_key in request.form:
            subject.review = True
        else:
            subject.review = False

        if recording_grades_key in request.form:
            subject.recording_grades = True
        else:
            subject.recording_grades = False

        if grade_entry_review_key in request.form:
            subject.grade_entry_review = True
        else:
            subject.grade_entry_review = False

        subject.notes = request.form.get(notes_key)

    db.session.commit()
    flash('Subjects updated successfully!', 'success')
    return redirect(url_for('list_subjects', control_id=control_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(role=Role.ADMIN).first()
        print(admin_user)
        if not admin_user:
            admin = User(username='a@admin.com', password='admin', role=Role.ADMIN)  # Hash password!
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
