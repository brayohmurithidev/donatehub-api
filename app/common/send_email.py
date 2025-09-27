from datetime import datetime

from fastapi_mail import MessageSchema, MessageType, FastMail, ConnectionConfig
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.logger import logger
from app.services.template_renderer import render_template


class SendEmailSchema(BaseModel):
    subject: str
    template: str
    context: dict


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_mail(email: EmailStr, data: SendEmailSchema):
    try:
        subject = data.subject
        template_name = data.template

        html_body = render_template(f"{template_name}.html.j2", data.context)

        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=html_body,  # use body for HTML content
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)

        logger.info(f"Email sent successfully → {email} | subject={subject}")
        return {"status": "success", "recipient": email, "subject": subject}

    except Exception as e:
        logger.error(f"Failed to send email → {email} | error={e}")
        return {"status": "failed", "recipient": email, "error": str(e)}


async def send_verification_email(email: EmailStr, payload: dict):
    # Generate verification url
    url = payload.get("verification_url", "http://fazilabs.com")
    context = {
        "user": {
            "name": payload.get("name", "User")
        },
        "verification_url": url,
        "logo_url": payload.get("logo_url", ""),
        "brand_name": "Donate Hub",
        "support_email": "support@fazilabs.com",
        "now_year": datetime.now().year
    }

    data = SendEmailSchema(
        context=context,
        template="email/email_verification",
        subject="Verify your email address"
    )

    result = await send_mail(email, data)
    return result
