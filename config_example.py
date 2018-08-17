from pathlib import Path

cwd = Path(__file__).resolve().parent / 'data'
if not cwd.exists():
    cwd.mkdir(mode=0o755, parents=True)

# If this is set to True, debug mode is turned on
DEBUG = True

# Don't change this
CSRF_ENABLED = True
SQLALCHEMY_TRACK_MODIFICATIONS = False  # No annoying warning

# Put random string value here
SECRET_KEY = 'VerySecretKey'

# Database URI. Change this if you don't want to use SQLite
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(cwd / 'app.db')

# Time to solve the test (in seconds)
TIME_TO_SOLVE = 3600

# Default admin password
ADMIN_PASSWORD = 'admin'
