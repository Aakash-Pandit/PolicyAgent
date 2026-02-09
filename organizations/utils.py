import os
import uuid

from fastapi import UploadFile

# Directory for storing uploaded policy files
UPLOAD_DIR = "uploads/policies"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def delete_file_if_exists(file_path: str | None) -> None:
    """Delete file path if it exists (handles relative paths)."""
    if not file_path:
        return
    if os.path.isabs(file_path):
        candidate_paths = [file_path]
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate_paths = [file_path, os.path.join(base_dir, file_path)]
    for candidate in candidate_paths:
        if os.path.exists(candidate):
            os.remove(candidate)
            break


async def save_upload_file(upload_file: UploadFile) -> str:
    """Save an uploaded file and return the file path."""
    file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    content = await upload_file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path
