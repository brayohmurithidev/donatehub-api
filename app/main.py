import os

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from app.api.deps import get_current_user
from app.api.routes import index as app_routes
from app.db.models.user import User

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "DonateHub"),
    version="1.0.0",
    description="A multitenant donation platform API",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1
    },
)

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5173",
    "https://donatehub-tenant.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to the DonateHub API!"}


@app.get('/me')
def get_profile(user: User = Depends(get_current_user)):
    return user


app.include_router(app_routes.router, prefix="/api/v1")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=400,
                        content={"detail": "Database integrity error. Possibly duplicate or invalid fields."})
