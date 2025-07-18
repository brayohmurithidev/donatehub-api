from fastapi import APIRouter, UploadFile, File, HTTPException

from app.lib.upload import upload_image

router = APIRouter()

ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"]
MAX_SIZE_MB= 5


@router.post("/image")
def upload_image_route(file: UploadFile = File(...)):
    # validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Must be .jpg, .png, or .webp")

    # Validate size
    contents = file.file.read()
    file.file.seek(0) # reset for cloudinary upload

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_SIZE_MB}MB")
    # Upload
    try:
        image_url = upload_image(file)
        return {"url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")