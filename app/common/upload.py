from uuid import UUID

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException

from app.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


def upload_image(file, folder, public_id: UUID):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            public_id=str(public_id),
            overwrite=True,
            folder=folder,
            use_filename=True,
            unique_filename=False,
            format="webp",
            quality="auto",
        )
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
