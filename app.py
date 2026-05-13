from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from uuid import uuid4
from datetime import datetime
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from models import db, User, Admin, Student, Company, PlacementDrive, Application
from database import init_database
from forms import (
    LoginForm, CompanyRegistrationForm, StudentRegistrationForm,
    CompanyProfileForm, StudentProfileForm, PlacementDriveForm,
    ApplicationForm, SearchForm, ResumeUploadForm, ChangePasswordForm
)

app = Flask(__name__)
init_database(app)

app.config.setdefault('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.context_processor
def inject_current_time():
    now = datetime.utcnow()
    fallback_url = url_for('home')

    if current_user.is_authenticated:
        if current_user.role == 'admin':
            fallback_url = url_for('admin_dashboard')
        elif current_user.role == 'company':
            fallback_url = url_for('company_dashboard')
        elif current_user.role == 'student':
            fallback_url = url_for('student_dashboard')

    referrer = request.referrer
    safe_referrer = None
    if referrer and referrer.startswith(request.host_url) and referrer != request.url:
        safe_referrer = referrer

    return {
        'current_time': now,
        'current_date': now.date(),
        'back_url': safe_referrer or fallback_url,
        'show_back': current_user.is_authenticated,
    }


@app.template_filter('safe_float')
def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def _is_pdf_file(file_storage):
    if not file_storage or not getattr(file_storage, 'filename', None):
        return False
    filename = file_storage.filename
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext == 'pdf'


def _save_student_resume(student, file_storage):
    if not _is_pdf_file(file_storage):
        raise ValueError('Please upload a PDF resume.')

    original_filename = secure_filename(file_storage.filename)
    if not original_filename:
        raise ValueError('Invalid resume filename.')

    unique_prefix = uuid4().hex
    stored_filename = f"student_{student.id}_{unique_prefix}_{original_filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
    file_storage.save(filepath)

    old_resume = student.resume_path
    student.resume_path = stored_filename

    if old_resume and old_resume != stored_filename:
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_resume)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

# Routes
@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'company':
            return redirect(url_for('company_dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
    return render_template('auth/login.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            # Check if company is approved
            if user.role == 'company':
                company = Company.query.filter_by(user_id=user.id).first()
                if not company or not company.is_approved:
                    flash('Your company registration is pending approval.', 'warning')
                    return redirect(url_for('login'))
            
            # Check if user is blacklisted
            if user.is_blacklisted:
                flash('Your account has been blacklisted. Contact administrator.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user)
            flash('Login successful!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'company':
                return redirect(url_for('company_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_company'))
        
        # Create user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            password=hashed_password,
            role='company'
        )
        db.session.add(user)
        db.session.flush()  # Get user.id
        
        # Create company profile
        company = Company(
            user_id=user.id,
            company_name=form.company_name.data,
            hr_name=form.hr_name.data,
            hr_contact=form.hr_contact.data,
            website=form.website.data,
            address=form.address.data,
            description=form.description.data,
            is_approved=False  # Needs admin approval
        )
        db.session.add(company)
        db.session.commit()
        
        flash('Company registration submitted for approval. You will be notified once approved.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register_company.html', form=form)

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_student'))
        
        # Create user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            password=hashed_password,
            role='student'
        )
        db.session.add(user)
        db.session.flush()
        
        # Create student profile
        student = Student(
            user_id=user.id,
            full_name=form.full_name.data,
            roll_number=form.roll_number.data,
            contact=form.contact.data,
            department=form.department.data,
            semester=form.semester.data,
            cgpa=form.cgpa.data,
            skills=form.skills.data,
            resume_path=None
        )
        db.session.add(student)
        db.session.commit()
        
        flash('Student registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register_student.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.role not in ['student', 'company']:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.get(current_user.id)
        if not user:
            flash('User account not found.', 'danger')
            return redirect(url_for('logout'))

        if not check_password_hash(user.password, form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))

        user.password = generate_password_hash(form.new_password.data)
        db.session.commit()

        flash('Password changed successfully.', 'success')
        if current_user.role == 'company':
            return redirect(url_for('company_dashboard'))
        return redirect(url_for('student_dashboard'))

    return render_template('auth/change_password.html', form=form)

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    # Get statistics
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    pending_companies = Company.query.filter_by(is_approved=False).count()
    pending_drives = PlacementDrive.query.filter_by(status='pending').count()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_companies=total_companies,
                         total_drives=total_drives,
                         total_applications=total_applications,
                         pending_companies=pending_companies,
                         pending_drives=pending_drives)

@app.route('/admin/companies')
@login_required
def admin_companies():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    search_form = SearchForm()
    companies = Company.query.all()
    
    # Handle search
    search_query = request.args.get('search', '')
    if search_query:
        companies = Company.query.filter(
            (Company.company_name.contains(search_query)) |
            (Company.hr_name.contains(search_query))
        ).all()
    
    return render_template('admin/companies.html', 
                         companies=companies, 
                         search_form=search_form)


@app.route('/admin/company/<int:company_id>')
@login_required
def admin_company_detail(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.get_or_404(company_id)
    return render_template('admin/company_detail.html', company=company)


@app.route('/admin/company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_company_edit(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.get_or_404(company_id)
    form = CompanyProfileForm(obj=company)

    if form.validate_on_submit():
        form.populate_obj(company)
        db.session.commit()
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('admin_company_detail', company_id=company.id))

    return render_template('admin/edit_company.html', form=form, company=company)


@app.route('/admin/company/<int:company_id>/delete', methods=['POST'])
@login_required
def admin_company_delete(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.get_or_404(company_id)
    user = User.query.get(company.user_id)

    drive_count = PlacementDrive.query.filter_by(company_id=company.id).count()
    if drive_count > 0:
        flash('Company cannot be deleted because it has placement drives.', 'warning')
        return redirect(url_for('admin_company_detail', company_id=company.id))

    db.session.delete(company)
    if user:
        db.session.delete(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Unable to delete this company due to existing references.', 'danger')
        return redirect(url_for('admin_company_detail', company_id=company.id))

    flash('Company deleted successfully.', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/company/<int:company_id>/approve')
@login_required
def approve_company(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.get_or_404(company_id)
    company.is_approved = True
    db.session.commit()
    
    flash(f'{company.company_name} has been approved.', 'success')
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('admin_companies'))

@app.route('/admin/company/<int:company_id>/reject')
@login_required
def reject_company(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.get_or_404(company_id)
    company.is_approved = False
    db.session.commit()
    
    flash(f'{company.company_name} has been rejected.', 'warning')
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('admin_companies'))

@app.route('/admin/company/<int:company_id>/blacklist')
@login_required
def blacklist_company(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.get_or_404(company_id)
    user = User.query.get(company.user_id)
    user.is_blacklisted = True
    db.session.commit()
    
    flash(f'{company.company_name} has been blacklisted.', 'danger')
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('admin_companies'))


@app.route('/admin/company/<int:company_id>/activate')
@login_required
def unblacklist_company(company_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.get_or_404(company_id)
    user = User.query.get(company.user_id)
    user.is_blacklisted = False
    db.session.commit()

    flash(f'{company.company_name} has been activated.', 'success')
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('admin_company_detail', company_id=company_id))

@app.route('/admin/students')
@login_required
def admin_students():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    search_form = SearchForm()
    students = Student.query.all()
    
    # Handle search
    search_query = request.args.get('search', '')
    if search_query:
        students = Student.query.filter(
            (Student.full_name.contains(search_query)) |
            (Student.roll_number.contains(search_query)) |
            (Student.contact.contains(search_query))
        ).all()
    
    return render_template('admin/students.html', 
                         students=students, 
                         search_form=search_form)


@app.route('/admin/student/<int:student_id>')
@login_required
def admin_student_detail(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    student = Student.query.get_or_404(student_id)
    return render_template('admin/student_detail.html', student=student)


@app.route('/admin/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_student_edit(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    student = Student.query.get_or_404(student_id)
    form = StudentProfileForm(obj=student)

    if form.validate_on_submit():
        student.full_name = form.full_name.data
        student.contact = form.contact.data
        student.department = form.department.data
        student.semester = form.semester.data
        student.cgpa = form.cgpa.data
        student.skills = form.skills.data
        db.session.commit()
        flash('Student profile updated successfully!', 'success')
        return redirect(url_for('admin_student_detail', student_id=student.id))

    return render_template('admin/edit_student.html', form=form, student=student)


@app.route('/admin/student/<int:student_id>/delete', methods=['POST'])
@login_required
def admin_student_delete(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)

    application_count = Application.query.filter_by(student_id=student.id).count()
    if application_count > 0:
        flash('Student cannot be deleted because they have applications.', 'warning')
        return redirect(url_for('admin_student_detail', student_id=student.id))

    resume_path = student.resume_path

    db.session.delete(student)
    if user:
        db.session.delete(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Unable to delete this student due to existing references.', 'danger')
        return redirect(url_for('admin_student_detail', student_id=student.id))

    if resume_path:
        resume_full_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_path)
        if os.path.exists(resume_full_path):
            try:
                os.remove(resume_full_path)
            except OSError:
                pass

    flash('Student deleted successfully.', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/student/<int:student_id>/blacklist')
@login_required
def blacklist_student(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    user.is_blacklisted = True
    db.session.commit()
    
    flash(f'{student.full_name} has been blacklisted.', 'danger')
    return redirect(url_for('admin_students'))


@app.route('/admin/student/<int:student_id>/activate')
@login_required
def unblacklist_student(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    user.is_blacklisted = False
    db.session.commit()

    flash(f'{student.full_name} has been activated.', 'success')
    return redirect(url_for('admin_student_detail', student_id=student_id))

@app.route('/admin/drives')
@login_required
def admin_drives():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    drives = PlacementDrive.query.all()
    current_date = datetime.utcnow().date()
    return render_template('admin/drives.html', drives=drives, current_date=current_date)


@app.route('/admin/drive/<int:drive_id>')
@login_required
def admin_drive_detail(drive_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    drive = PlacementDrive.query.get_or_404(drive_id)
    return render_template('admin/drive_detail.html', drive=drive)

@app.route('/admin/drive/<int:drive_id>/approve')
@login_required
def approve_drive(drive_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.application_deadline < datetime.utcnow().date():
        flash('Cannot approve an expired placement drive.', 'warning')
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('admin_drives'))
    drive.status = 'approved'
    db.session.commit()
    
    flash(f'Drive "{drive.job_title}" has been approved.', 'success')
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('admin_drives'))

@app.route('/admin/drive/<int:drive_id>/reject')
@login_required
def reject_drive(drive_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'rejected'
    db.session.commit()
    
    flash(f'Drive "{drive.job_title}" has been rejected.', 'warning')
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('admin_drives'))

@app.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    applications = Application.query.all()
    return render_template('admin/applications.html', applications=applications)

# Company Routes
@app.route('/company/dashboard')
@login_required
def company_dashboard():
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        flash('Company profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    # Get company statistics
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    today = datetime.utcnow().date()
    active_drives = (PlacementDrive.query
                    .filter(
                        PlacementDrive.company_id == company.id,
                        PlacementDrive.status == 'approved',
                        PlacementDrive.application_deadline >= today,
                    )
                    .order_by(PlacementDrive.application_deadline.asc())
                    .all())
    total_drives = len(drives)
    total_applicants = 0
    for drive in drives:
        total_applicants += Application.query.filter_by(drive_id=drive.id).count()
    
    return render_template('company/dashboard.html',
                         company=company,
                         drives=drives,
                         active_drives=active_drives,
                         total_drives=total_drives,
                         total_applicants=total_applicants)

@app.route('/company/profile', methods=['GET', 'POST'])
@login_required
def company_profile():
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        flash('Company profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    form = CompanyProfileForm(obj=company)
    if form.validate_on_submit():
        form.populate_obj(company)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('company_profile'))
    
    return render_template('company/profile.html', form=form, company=company)

@app.route('/company/drive/create', methods=['GET', 'POST'])
@login_required
def create_drive():
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company or not company.is_approved:
        flash('Your company is not approved to create placement drives.', 'warning')
        return redirect(url_for('company_dashboard'))
    
    form = PlacementDriveForm()
    if form.validate_on_submit():
        drive = PlacementDrive(
            company_id=company.id,
            job_title=form.job_title.data,
            job_description=form.job_description.data,
            eligibility_criteria=f"{form.eligibility_criteria.data:.2f}",
            location=form.location.data,
            salary_package=form.salary_package.data,
            application_deadline=form.application_deadline.data,
            status='pending'  # Needs admin approval
        )
        db.session.add(drive)
        db.session.commit()
        
        flash('Placement drive created successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('company/create_drive.html', form=form)


@app.route('/company/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_drive(drive_id):
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company or not company.is_approved:
        flash('Your company is not approved to manage placement drives.', 'warning')
        return redirect(url_for('company_dashboard'))

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company_dashboard'))

    if drive.status == 'closed':
        flash('Closed drives cannot be edited.', 'warning')
        return redirect(url_for('company_dashboard'))

    form = PlacementDriveForm(obj=drive)
    if form.validate_on_submit():
        drive.job_title = form.job_title.data
        drive.job_description = form.job_description.data
        drive.eligibility_criteria = f"{form.eligibility_criteria.data:.2f}"
        drive.location = form.location.data
        drive.salary_package = form.salary_package.data
        drive.application_deadline = form.application_deadline.data
        drive.status = 'pending'
        db.session.commit()

        flash('Placement drive updated and sent for admin approval.', 'success')
        return redirect(url_for('company_dashboard'))

    return render_template('company/edit_drive.html', form=form, drive=drive)


@app.route('/company/drive/<int:drive_id>/close', methods=['POST'])
@login_required
def close_drive(drive_id):
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company or not company.is_approved:
        flash('Your company is not approved to manage placement drives.', 'warning')
        return redirect(url_for('company_dashboard'))

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company_dashboard'))

    if drive.status == 'closed':
        flash('Drive is already closed.', 'info')
        return redirect(url_for('company_dashboard'))

    drive.status = 'closed'
    db.session.commit()
    flash('Placement drive closed successfully.', 'success')
    return redirect(url_for('company_dashboard'))


@app.route('/company/drive/<int:drive_id>/delete', methods=['POST'])
@login_required
def delete_drive(drive_id):
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company or not company.is_approved:
        flash('Your company is not approved to manage placement drives.', 'warning')
        return redirect(url_for('company_dashboard'))

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company_dashboard'))

    application_count = Application.query.filter_by(drive_id=drive.id).count()
    if application_count > 0:
        flash('This drive cannot be deleted because it has applications.', 'warning')
        return redirect(url_for('company_dashboard'))

    if drive.status == 'approved':
        flash('Approved drives cannot be deleted. Please close the drive instead.', 'warning')
        return redirect(url_for('company_dashboard'))

    db.session.delete(drive)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Unable to delete this drive due to existing references.', 'danger')
        return redirect(url_for('company_dashboard'))

    flash('Placement drive deleted successfully.', 'success')
    return redirect(url_for('company_dashboard'))

@app.route('/company/drive/<int:drive_id>/applications')
@login_required
def view_drive_applications(drive_id):
    if current_user.role != 'company':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    company = Company.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if drive belongs to company
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company_dashboard'))
    
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template('company/view_applications.html',
                         drive=drive,
                         applications=applications)

@app.route('/company/application/<int:app_id>/update_status', methods=['POST'])
@login_required
def update_application_status(app_id):
    if current_user.role != 'company':
        return jsonify({'success': False, 'message': 'Access denied'})

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'message': 'Company profile not found'})

    application = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.get(application.drive_id)
    if not drive:
        return jsonify({'success': False, 'message': 'Drive not found'})

    if drive.company_id != company.id:
        return jsonify({'success': False, 'message': 'Access denied'})

    if drive.status not in ['approved', 'closed']:
        return jsonify({'success': False, 'message': 'Drive is not available for selection'})

    new_status = request.form.get('status')
    if new_status not in ['applied', 'shortlisted', 'selected', 'rejected']:
        return jsonify({'success': False, 'message': 'Invalid status'})

    if application.status == 'selected' and new_status == 'shortlisted':
        return jsonify({'success': False, 'message': 'This application is already Selected and cannot be changed back to Shortlisted.'})

    application.status = new_status

    # Handle interview link and remarks when selecting a student
    if new_status == 'selected':
        interview_link = request.form.get('interview_link')
        interview_remarks = request.form.get('interview_remarks')
        if interview_link:
            application.interview_link = interview_link
        if interview_remarks:
            application.interview_remarks = interview_remarks

    db.session.commit()
    return jsonify({'success': True, 'message': 'Status updated'})

# Student Routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    # Get approved drives
    today = datetime.utcnow().date()
    approved_drives = (PlacementDrive.query
                      .filter(PlacementDrive.status == 'approved', PlacementDrive.application_deadline >= today)
                      .order_by(PlacementDrive.application_deadline.asc())
                      .all())

    closed_drives = (PlacementDrive.query
                    .filter(
                        (PlacementDrive.status == 'closed') |
                        ((PlacementDrive.status == 'approved') & (PlacementDrive.application_deadline < today))
                    )
                    .order_by(PlacementDrive.application_deadline.desc())
                    .all())
    
    # Get student's applications
    applications = Application.query.filter_by(student_id=student.id).all()

    resume_form = ResumeUploadForm()
    
    return render_template('student/dashboard.html',
                         student=student,
                         drives=approved_drives,
                         closed_drives=closed_drives,
                         applications=applications,
                         resume_form=resume_form,
                         current_date=datetime.utcnow().date())


@app.route('/student/resume/upload', methods=['POST'])
@login_required
def student_resume_upload():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('logout'))

    form = ResumeUploadForm()
    if not form.validate_on_submit():
        flash('Please choose a resume file to upload.', 'danger')
        return redirect(url_for('student_dashboard'))

    try:
        _save_student_resume(student, form.resume.data)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('student_dashboard'))

    db.session.commit()
    flash('Resume uploaded successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    form = StudentProfileForm(obj=student)
    if form.validate_on_submit():
        # Handle resume upload
        if form.resume.data:
            try:
                _save_student_resume(student, form.resume.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('student_profile'))

        student.full_name = form.full_name.data
        student.contact = form.contact.data
        student.department = form.department.data
        student.semester = form.semester.data
        student.cgpa = form.cgpa.data
        student.skills = form.skills.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))
    
    return render_template('student/profile.html', form=form, student=student)

@app.route('/student/drives')
@login_required
def view_drives():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    today = datetime.utcnow().date()
    drives = (PlacementDrive.query
             .filter(PlacementDrive.status == 'approved', PlacementDrive.application_deadline >= today)
             .order_by(PlacementDrive.application_deadline.asc())
             .all())
    
    # Check which drives student has already applied to
    applied_drive_ids = [app.drive_id for app in 
                        Application.query.filter_by(student_id=student.id).all()]
    
    return render_template('student/view_drives.html',
                         student=student,
                         drives=drives,
                         applied_drive_ids=applied_drive_ids)

@app.route('/student/apply/<int:drive_id>', methods=['POST'])
@login_required
def apply_for_drive(drive_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if drive is approved
    if drive.status != 'approved':
        flash('This drive is not available for applications.', 'warning')
        return redirect(url_for('view_drives'))

    if drive.application_deadline < datetime.utcnow().date():
        flash('Applications for this drive are closed (deadline has passed).', 'warning')
        return redirect(url_for('view_drives'))
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()
    
    if existing_application:
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('view_drives'))
    
    # Check eligibility based on CGPA
    try:
        min_cgpa_required = float(drive.eligibility_criteria)
    except (TypeError, ValueError):
        flash('This placement drive has invalid eligibility criteria. Please contact the administrator.', 'danger')
        return redirect(url_for('view_drives'))

    if student.cgpa < min_cgpa_required:
        flash('You do not meet the eligibility criteria for this drive.', 'danger')
        return redirect(url_for('view_drives'))
    
    # Create application
    application = Application(
        student_id=student.id,
        drive_id=drive_id,
        status='applied',
        drive_job_title=drive.job_title,
        drive_job_description=drive.job_description,
        drive_location=drive.location,
        drive_salary_package=drive.salary_package,
        drive_application_deadline=drive.application_deadline,
        drive_eligibility_criteria=drive.eligibility_criteria,
        applied_date=datetime.utcnow()
    )
    db.session.add(application)
    db.session.commit()
    
    flash(f'Successfully applied for {drive.job_title}!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/applications')
@login_required
def student_applications():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    applications = Application.query.filter_by(student_id=student.id).all()
    
    return render_template('student/applications.html', applications=applications)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', message='Internal server error'), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    flash('Uploaded file is too large. Maximum size is 5 MB.', 'danger')
    if current_user.is_authenticated and current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('home'))

# Create database tables and admin user
def create_tables():
    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        existing_columns = {col['name'] for col in inspector.get_columns('applications')}
        snapshot_columns = {
            'drive_job_title': 'VARCHAR(200)',
            'drive_job_description': 'TEXT',
            'drive_location': 'VARCHAR(100)',
            'drive_salary_package': 'VARCHAR(50)',
            'drive_application_deadline': 'DATE',
            'drive_eligibility_criteria': 'VARCHAR(50)',
        }

        missing = [name for name in snapshot_columns.keys() if name not in existing_columns]
        if missing:
            for name in missing:
                col_type = snapshot_columns[name]
                try:
                    db.session.execute(text(f"ALTER TABLE applications ADD COLUMN {name} {col_type}"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # Best-effort backfill: snapshot current drive data for older applications that don't have snapshots.
        try:
            apps_to_backfill = Application.query.filter(Application.drive_job_title.is_(None)).all()
            if apps_to_backfill:
                for application in apps_to_backfill:
                    drive = PlacementDrive.query.get(application.drive_id)
                    if not drive:
                        continue
                    application.drive_job_title = drive.job_title
                    application.drive_job_description = drive.job_description
                    application.drive_location = drive.location
                    application.drive_salary_package = drive.salary_package
                    application.drive_application_deadline = drive.application_deadline
                    application.drive_eligibility_criteria = drive.eligibility_criteria
                db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Check if admin exists
        admin_user = User.query.filter_by(email='admin@placement.com').first()
        if not admin_user:
            admin_user = User(
                email='admin@placement.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.flush()  # Ensure admin_user.id is assigned before creating Admin
            
            # Create admin profile
            admin = Admin(
                user_id=admin_user.id,
                full_name='Administrator'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin@placement.com / admin123")
        else:
            admin_profile = Admin.query.filter_by(user_id=admin_user.id).first()
            if not admin_profile:
                admin = Admin(
                    user_id=admin_user.id,
                    full_name='Administrator'
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin profile created for existing admin user: admin@placement.com")

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)