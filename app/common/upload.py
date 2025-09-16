from uuid import UUID

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.common.handle_error import handle_error
from app.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def upload_image(file, folder, public_id: UUID):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            public_id=str(public_id),
            overwrite=True,
            folder=folder,
            use_filename=True,
            unique_filename=False,
            invalidate=True,
            format="webp",
            quality="auto",
        )
        # Force a stable URL with no Version number
        stable_url = f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/{result['secure_url'].split('/')[-2]}/{result['secure_url'].split('/')[-1]}"
        return stable_url
    except Exception as e:
        handle_error(500, "Image upload failed", e)


# upload_documents
def upload_documents(upload_file: UploadFile, folder: str, public_id: str):
    # validate
    if upload_file.content_type not in ALLOWED_TYPES:
        handle_error(400, "Unsupported file type. Must be .jpg, .png, or .pdf")
    try:
        result = cloudinary.uploader.upload(
            upload_file.file,
            public_id=str(public_id),
            overwrite=True,
            folder=folder,
            use_filename=True,
            unique_filename=False,
            invalidate=True,
            resource_type="auto",
        )
        stable_url = f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/{result['secure_url'].split('/')[-2]}/{result['secure_url'].split('/')[-1]}"
        return stable_url
    except Exception as e:
        handle_error(500, "Document upload failed", e)
