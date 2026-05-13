import os

from models import db


def configure_app(app):
    secret_key = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secret_key
    if not app.config.get('WTF_CSRF_SECRET_KEY'):
        app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']

    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///placement_portal.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    if not app.config.get('UPLOAD_FOLDER'):
        app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')


def init_database(app):
    configure_app(app)
    db.init_app(app)
