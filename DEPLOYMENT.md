# Deployment Guide for AJX11 Placement Portal

This guide covers multiple deployment options for your Flask placement portal.

## Prerequisites

Before deploying, ensure you have:
- Git installed and repository pushed to GitHub
- All dependencies listed in `requirements.txt`
- Python 3.11+ installed locally for testing

## Deployment Options

### Option 1: Render (Recommended - Free Tier Available)

Render is a modern cloud platform with a generous free tier, perfect for Flask applications.

#### Steps:

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Sign up for Render**:
   - Go to [https://render.com](https://render.com)
   - Sign up with your GitHub account

3. **Create a New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `arjitjaiswal08-art/AJX11_Placement_portal`
   - Configure the service:
     - **Name**: `placement-portal` (or your choice)
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: `Free`

4. **Add Environment Variables** (Optional):
   - Go to "Environment" tab
   - Add `SECRET_KEY` with a random string value
   - Add `FLASK_ENV=production`

5. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically deploy your app
   - Your app will be available at: `https://placement-portal.onrender.com`

#### Notes:
- Free tier apps sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- SQLite database will persist on the instance
- For production, consider upgrading to paid tier with PostgreSQL

---

### Option 2: Railway (Easy Deployment)

Railway offers simple deployment with automatic HTTPS and custom domains.

#### Steps:

1. **Sign up for Railway**:
   - Go to [https://railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure**:
   - Railway auto-detects Python
   - Add environment variables if needed:
     - `SECRET_KEY`: your-secret-key
     - `FLASK_ENV`: production

4. **Deploy**:
   - Railway automatically deploys
   - Get your URL from the "Settings" tab

---

### Option 3: PythonAnywhere (Beginner Friendly)

PythonAnywhere is great for beginners and offers a free tier.

#### Steps:

1. **Sign up**:
   - Go to [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
   - Create a free account

2. **Clone Repository**:
   - Open a Bash console
   - Run:
     ```bash
     git clone https://github.com/arjitjaiswal08-art/AJX11_Placement_portal.git
     cd AJX11_Placement_portal
     ```

3. **Create Virtual Environment**:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 placement-env
   pip install -r requirements.txt
   ```

4. **Configure Web App**:
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Manual configuration" → Python 3.10
   - Set source code directory: `/home/yourusername/AJX11_Placement_portal`
   - Edit WSGI file:
     ```python
     import sys
     path = '/home/yourusername/AJX11_Placement_portal'
     if path not in sys.path:
         sys.path.append(path)
     
     from app import app as application
     ```

5. **Reload** and visit your site at: `yourusername.pythonanywhere.com`

---

### Option 4: Heroku (Classic Option)

Heroku is a well-established platform (requires credit card for free tier).

#### Steps:

1. **Install Heroku CLI**:
   ```bash
   brew install heroku/brew/heroku  # macOS
   ```

2. **Login**:
   ```bash
   heroku login
   ```

3. **Create App**:
   ```bash
   heroku create placement-portal-ajx11
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Open App**:
   ```bash
   heroku open
   ```

---

### Option 5: Vercel (Serverless)

Vercel is great for serverless deployments but has limitations with SQLite.

#### Steps:

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel
   ```

3. **Follow prompts** and your app will be deployed

**Note**: Vercel's serverless nature means SQLite won't persist. Consider using a cloud database like PostgreSQL or MongoDB.

---

## Post-Deployment Checklist

After deploying to any platform:

1. **Test the application**:
   - Visit the deployed URL
   - Test login with admin credentials: `admin@placement.com` / `admin123`
   - Test student and company registration
   - Test file uploads

2. **Set up custom domain** (optional):
   - Most platforms allow custom domain configuration
   - Follow platform-specific documentation

3. **Monitor logs**:
   - Check application logs for errors
   - Set up error monitoring (Sentry, etc.)

4. **Database backups**:
   - For production, set up regular database backups
   - Consider migrating from SQLite to PostgreSQL for better reliability

5. **Security**:
   - Change default admin password
   - Set strong SECRET_KEY in environment variables
   - Enable HTTPS (most platforms do this automatically)

---

## Troubleshooting

### Common Issues:

1. **Module not found errors**:
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **Database not persisting**:
   - SQLite may not work on serverless platforms
   - Migrate to PostgreSQL or MySQL

3. **File uploads not working**:
   - Check upload folder permissions
   - Consider using cloud storage (AWS S3, Cloudinary)

4. **App sleeping/slow start**:
   - Free tiers often sleep after inactivity
   - Upgrade to paid tier or use uptime monitoring services

---

## Recommended: Render Deployment

For this project, **Render** is recommended because:
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy GitHub integration
- ✅ Persistent storage for SQLite
- ✅ Simple environment variable management
- ✅ Automatic deployments on git push

---

## Need Help?

If you encounter issues:
1. Check platform-specific documentation
2. Review application logs
3. Verify all environment variables are set
4. Test locally first: `python app.py`

Good luck with your deployment! 🚀
