# AJX11 Placement Portal

A comprehensive placement management system built with Flask for managing student placements, company registrations, and placement drives.

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
```bash
git clone https://github.com/arjitjaiswal08-art/AJX11_Placement_portal.git
cd AJX11_Placement_portal
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the application**:
```bash
python app.py
```

5. **Access the application**:
   - Open browser and go to: http://localhost:5000
   - **Admin login**: admin@placement.com / admin123

## 🌐 Deployment

Ready to deploy? Check out our comprehensive [DEPLOYMENT.md](DEPLOYMENT.md) guide!

**Quick Deploy Options**:
- **Render** (Recommended) - Free tier with persistent storage
- **Railway** - Simple deployment with auto-scaling
- **PythonAnywhere** - Beginner-friendly hosting
- **Heroku** - Classic PaaS platform
- **Vercel** - Serverless deployment

### Quick Deploy to Render:
1. Push your code to GitHub
2. Sign up at [render.com](https://render.com)
3. Create new Web Service from your GitHub repo
4. Deploy with one click!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

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