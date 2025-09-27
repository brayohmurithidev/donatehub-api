from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DonateHub"
    ENV: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    DATABASE_URL: str
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    MPESA_CONSUMER_KEY: str
    MPESA_CONSUMER_SECRET: str
    MPESA_SHORTCODE: str
    MPESA_PASSKEY: str
    ENCRYPTION_SECRET_KEY: str
    RABBITMQ_URL: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: str
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    FRONTEND_URL: HttpUrl

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
