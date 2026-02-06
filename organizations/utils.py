import os
import uuid

from fastapi import UploadFile

# Directory for storing uploaded policy files
UPLOAD_DIR = "uploads/policies"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> str:
    """Save an uploaded file and return the file path."""
    file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    content = await upload_file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path
