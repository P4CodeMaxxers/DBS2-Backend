from flask import Flask, request
from flask_login import LoginManager
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()


# Setup of key Flask object (app)

# Use relative instance path when running locally, /app/instance when in Docker
instance_path = os.environ.get('INSTANCE_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')

app = Flask(
    __name__,
    instance_path=instance_path,
    instance_relative_config=True
)

# Configure Flask Port, default to 8403 which is same as Docker setup
app.config['FLASK_PORT'] = int(os.environ.get('FLASK_PORT') or 8403)

# Configure Flask to handle JSON with UTF-8 encoding versus default ASCII
app.config['JSON_AS_ASCII'] = False  # Allow emojis, non-ASCII characters in JSON responses


# Initialize Flask-Login object
login_manager = LoginManager()
login_manager.init_app(app)


# Allowed servers for cross-origin resource sharing (CORS)
cors = CORS(
   app,
   supports_credentials=True,
   origins=[
       'http://localhost:4500',
       'http://127.0.0.1:4500',
       'http://localhost:4600',
       'http://127.0.0.1:4600',
       'http://localhost:4000',
       'http://127.0.0.1:4000',
       'https://open-coding-society.github.io',
       'https://pages.opencodingsociety.com',
       'https://p4codemaxxers.github.io'
   ],
   methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
   allow_headers=["Content-Type", "Authorization", "X-Origin", "Cache-Control", "Pragma"]
)

# Ensure CORS on every response (including 500) so frontend can see errors from localhost:4600 -> 8403
CORS_ORIGINS = [
    'http://localhost:4500', 'http://127.0.0.1:4500',
    'http://localhost:4600', 'http://127.0.0.1:4600',
    'http://localhost:4000', 'http://127.0.0.1:4000',
    'https://open-coding-society.github.io',
    'https://pages.opencodingsociety.com',
    'https://p4codemaxxers.github.io'
]

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin') or getattr(request, 'origin', None)
    if origin and origin in CORS_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Origin, Cache-Control, Pragma'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response


@app.errorhandler(500)
def handle_500(err):
    """Return JSON 500 with error message so admin/API clients can see the cause; CORS is applied in after_request."""
    import traceback
    from flask import jsonify
    tb = traceback.format_exc()
    body = {'error': 'Internal Server Error', 'message': str(err)}
    if app.debug or os.environ.get('FLASK_DEBUG'):
        body['traceback'] = tb
    return jsonify(body), 500


# Admin Defaults
app.config['ADMIN_USER'] = os.environ.get('ADMIN_USER') or 'Admin Name'
app.config['ADMIN_UID'] = os.environ.get('ADMIN_UID') or 'admin'
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD') or os.environ.get('DEFAULT_PASSWORD') or 'password'
app.config['ADMIN_PFP'] = os.environ.get('ADMIN_PFP') or 'default.png'
# Default User Defaults
app.config['DEFAULT_USER'] = os.environ.get('DEFAULT_USER') or 'User Name'
app.config['DEFAULT_UID'] = os.environ.get('DEFAULT_UID') or 'user'
app.config['DEFAULT_USER_PASSWORD'] = os.environ.get('DEFAULT_USER_PASSWORD') or os.environ.get('DEFAULT_PASSWORD') or 'password'
app.config['DEFAULT_USER_PFP'] = os.environ.get('DEFAULT_USER_PFP') or 'default.png'
# Reset Defaults
app.config['DEFAULT_PASSWORD'] = os.environ.get('DEFAULT_PASSWORD') or 'password'
app.config['DEFAULT_PFP'] = os.environ.get('DEFAULT_PFP') or 'default.png'


# Browser settings
# SECRET_KEY is required for JWT/sessions; use env in production, dev fallback for local (avoids "Expected a string value" on login)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME') or 'sess_python_flask'
JWT_TOKEN_NAME = os.environ.get('JWT_TOKEN_NAME') or 'jwt_python_flask'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = SESSION_COOKIE_NAME
app.config['JWT_TOKEN_NAME'] = JWT_TOKEN_NAME

# Cross-origin cookie support for authentication
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Database settings
IS_PRODUCTION = os.environ.get('IS_PRODUCTION') or None
dbName = 'user_management'
DB_ENDPOINT = os.environ.get('DB_ENDPOINT') or None
DB_USERNAME = os.environ.get('DB_USERNAME') or None
DB_PASSWORD = os.environ.get('DB_PASSWORD') or None
if DB_ENDPOINT and DB_USERNAME and DB_PASSWORD:
   # Production - Use MySQL
   DB_PORT = '3306'
   DB_NAME = dbName
   dbString = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}'
   dbURI =  dbString + '/' + dbName
   backupURI = None  # MySQL backup would require a different approach
else:
   # Development - Use SQLite
   dbString = 'sqlite:///volumes/'
   dbURI = dbString + dbName + '.db'
   backupURI = dbString + dbName + '_bak.db'
# Set database configuration in Flask app
app.config['DB_ENDPOINT'] = DB_ENDPOINT
app.config['DB_USERNAME'] = DB_USERNAME
app.config['DB_PASSWORD'] = DB_PASSWORD
app.config['SQLALCHEMY_DATABASE_NAME'] = dbName
app.config['SQLALCHEMY_DATABASE_STRING'] = dbString
app.config['SQLALCHEMY_DATABASE_URI'] = dbURI
app.config['SQLALCHEMY_BACKUP_URI'] = backupURI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Image upload settings
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # maximum size of uploaded content
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']  # supported file types
app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Data folder for shared file-based storage
app.config['DATA_FOLDER'] = os.path.join(app.instance_path, 'data')
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)


# GITHUB settings
app.config['GITHUB_API_URL'] = 'https://api.github.com'
app.config['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN') or None
app.config['GITHUB_TARGET_TYPE'] = os.environ.get('GITHUB_TARGET_TYPE') or 'user'
app.config['GITHUB_TARGET_NAME'] = os.environ.get('GITHUB_TARGET_NAME') or 'open-coding-society'


# Gemini API settingsa
app.config['GEMINI_SERVER'] = os.environ.get('GEMINI_SERVER') or 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY') or None


# KASM settings
app.config['KASM_SERVER'] = os.environ.get('KASM_SERVER') or 'https://kasm.opencodingsociety.com'
app.config['KASM_API_KEY'] = os.environ.get('KASM_API_KEY') or None
app.config['KASM_API_KEY_SECRET'] = os.environ.get('KASM_API_KEY_SECRET') or None


#GROQ settings
app.config['GROQ_API_KEY'] = os.environ.get('GROQ_API_KEY')

from flask import current_app

@app.cli.group()
def custom():
    """Custom commands."""
    pass


