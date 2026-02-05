from fastapi import APIRouter, BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from app.config import settings
from app.models import LeadCreate

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

@router.post("")
async def submit_lead(lead: LeadCreate, background_tasks: BackgroundTasks):
    # Honeypot check
    if lead.website_url:
        # If populated, it's likely a bot. Return success but do nothing.
        return {"status": "ok", "message": "Request submitted successfully"}

    message = MessageSchema(
        subject="New Lead from Mitra Website",
        recipients=[settings.ADMIN_EMAIL],
        body=f"""
New Lead Received:

Name: {lead.name}
Email: {lead.email}
Phone: {lead.phone}

Details:
{lead.details}
        """,
        subtype=MessageType.plain
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    return {"status": "ok", "message": "Request submitted successfully"}
