Install dependencies:

bash
pip install -r requirements.txt
Run the application:

bash
python app.py
Access the application:

Open browser and go to: http://localhost:5000

Admin login: admin@placement.com / admin123

Features Implemented:
✅ Core Features:
Authentication System - Login for all roles, registration for Company/Student

Admin Functionalities:

Approve/reject company registrations

Approve/reject placement drives

View/manage all entities

Search functionality

Blacklist students/companies

Dashboard with statistics

Company Functionalities:

Registration with admin approval

Create/edit placement drives

View student applications

Update application status

Company profile management

Student Functionalities:

Self-registration

View approved drives

Apply for drives (prevents duplicate applications)

View application status

Profile management

Other Features:

Prevent multiple applications

Only approved companies can create drives

Role-based access control

Complete application history

Responsive Bootstrap UI

✅ Database Features:
Programmatically created SQLite database

All required tables with relationships

Proper constraints and validations

The application is fully functional and ready to use. All features work as specified in the requirements without using JavaScript for core functionality (though minimal JavaScript is used for Bootstrap components).