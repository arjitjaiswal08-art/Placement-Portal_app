#!/bin/bash

# Deployment script for AJX11 Placement Portal
# This script helps you push your code to GitHub

echo "🚀 AJX11 Placement Portal - Deployment Helper"
echo "=============================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not initialized!"
    echo "Run: git init"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 You have uncommitted changes."
    echo ""
    git status -s
    echo ""
    read -p "Do you want to commit these changes? (y/n): " commit_choice
    
    if [ "$commit_choice" = "y" ]; then
        read -p "Enter commit message: " commit_msg
        git add .
        git commit -m "$commit_msg"
        echo "✅ Changes committed!"
    else
        echo "⚠️  Skipping commit. Please commit manually."
    fi
else
    echo "✅ No uncommitted changes."
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo ""
    echo "❌ No remote repository configured!"
    echo "Add your GitHub repository:"
    echo "git remote add origin https://github.com/arjitjaiswal08-art/AJX11_Placement_portal.git"
    exit 1
fi

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git push origin main || git push origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Go to https://render.com and sign up"
    echo "2. Create a new Web Service"
    echo "3. Connect your GitHub repository"
    echo "4. Use these settings:"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: gunicorn app:app"
    echo "5. Deploy and get your live URL!"
    echo ""
    echo "📖 For detailed instructions, see DEPLOYMENT.md"
else
    echo ""
    echo "❌ Push failed! Please check your git configuration."
fi
