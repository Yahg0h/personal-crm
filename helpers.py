import os 
import uuid
from flask import redirect, session, url_for
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

# Allowed file extensions for uploaded files
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, upload_folder):
    MAX_FILE_SIZE = 5 * 1024 * 1024

    if file.content_length and file.content_length > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 5MB limit.")

    if file and allowed_file(file.filename):
        # Generate a unique filename using uuid
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return url_for("static", filename=f"uploads/photos/{filename}")
    else:
        raise ValueError("Invalid file type. Allowed types are: png, jpg, jpeg, webp.")