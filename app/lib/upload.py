import cloudinary
import cloudinary.uploader

from app.config import settings

cloudinary.config(
    cloud_name = settings.cloudinary_cloud_name,
    api_key = settings.cloudinary_api_key,
    api_secret = settings.cloudinary_api_secret,
    secure = True,
)

def upload_image(file, folder="campaigns"):
    result = cloudinary.uploader.upload(
        file.file,
        folder=folder,
        use_filename=True,
        unique_filename=True,
    )
    return result["secure_url"]