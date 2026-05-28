#!/usr/bin/env python3
"""
Quick test script to verify database initialization works correctly
"""

import os
import sys

# Remove existing database for clean test
db_path = 'instance/placement_portal.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ Removed existing database: {db_path}")

# Import app (this should trigger init_db())
print("\n🔄 Importing app and initializing database...")
from app import app, db, User, Admin

# Verify tables were created
with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n✓ Database initialized successfully!")
    print(f"✓ Tables created: {', '.join(tables)}")
    
    # Verify admin user exists
    admin_user = User.query.filter_by(email='admin@placement.com').first()
    if admin_user:
        print(f"✓ Admin user exists: {admin_user.email}")
        admin_profile = Admin.query.filter_by(user_id=admin_user.id).first()
        if admin_profile:
            print(f"✓ Admin profile exists: {admin_profile.full_name}")
        else:
            print("✗ Admin profile NOT found!")
            sys.exit(1)
    else:
        print("✗ Admin user NOT found!")
        sys.exit(1)

print("\n✅ All checks passed! Database is ready.")
print("\n🚀 You can now run: python app.py")
