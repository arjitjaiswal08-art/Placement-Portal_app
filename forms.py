from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FloatField, IntegerField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from wtforms.fields import FileField
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password')]
    )

class CompanyRegistrationForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(min=2, max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    hr_name = StringField('HR Name', validators=[DataRequired(), Length(min=2, max=100)])
    hr_contact = StringField('HR Contact', validators=[DataRequired(), Length(min=10, max=20)])
    website = StringField('Website', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    description = TextAreaField('Company Description', validators=[Optional()])

class StudentRegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(min=3, max=20)])
    contact = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=20)])
    department = SelectField('Department', choices=[
        ('CSE', 'Computer Science'),
        ('IT', 'Information Technology'),
        ('ECE', 'Electronics'),
        ('EEE', 'Electrical'),
        ('MECH', 'Mechanical'),
        ('CIVIL', 'Civil')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        (1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'),
        (5, '5th'), (6, '6th'), (7, '7th'), (8, '8th')
    ], validators=[DataRequired()], coerce=int)
    cgpa = FloatField('CGPA', validators=[DataRequired()])
    skills = TextAreaField('Skills', validators=[Optional()])

class CompanyProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(min=2, max=200)])
    hr_name = StringField('HR Name', validators=[DataRequired(), Length(min=2, max=100)])
    hr_contact = StringField('HR Contact', validators=[DataRequired(), Length(min=10, max=20)])
    website = StringField('Website', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    description = TextAreaField('Company Description', validators=[Optional()])

class StudentProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=20)])
    department = SelectField('Department', choices=[
        ('CSE', 'Computer Science'),
        ('IT', 'Information Technology'),
        ('ECE', 'Electronics'),
        ('EEE', 'Electrical'),
        ('MECH', 'Mechanical'),
        ('CIVIL', 'Civil')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        (1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'),
        (5, '5th'), (6, '6th'), (7, '7th'), (8, '8th')
    ], validators=[DataRequired()], coerce=int)
    cgpa = FloatField('CGPA', validators=[DataRequired()])
    skills = TextAreaField('Skills', validators=[Optional()])
    resume = FileField('Upload Resume')


class ResumeUploadForm(FlaskForm):
    resume = FileField('Upload Resume', validators=[DataRequired()])

class PlacementDriveForm(FlaskForm):
    job_title = StringField('Job Title', validators=[DataRequired(), Length(min=2, max=200)])
    job_description = TextAreaField('Job Description', validators=[DataRequired()])
    eligibility_criteria = FloatField('Minimum CGPA Required', validators=[DataRequired(), NumberRange(min=0, max=10)])
    location = StringField('Job Location', validators=[DataRequired()])
    salary_package = StringField('Salary Package', validators=[DataRequired()])
    application_deadline = DateField('Application Deadline', validators=[DataRequired()])
    
    def validate_application_deadline(self, field):
        if field.data < datetime.now().date():
            raise ValidationError('Deadline must be in the future.')

class ApplicationForm(FlaskForm):
    cover_letter = TextAreaField('Cover Letter', validators=[Optional()])

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[Optional()])