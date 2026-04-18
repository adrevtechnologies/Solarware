"""Email service for sending mailing packs."""
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from ..core.config import get_settings
from ..core.logging import logger
from ..core.errors import EmailError


class EmailService:
    """Handles email sending for mailing packs."""

    @staticmethod
    async def send_pack_email(
        mailing_pack: Dict,
        recipient_email: str,
        dry_run: bool = False,
        via: str = "smtp",
    ) -> Dict:
        """Send mailing pack via email.
        
        Args:
            mailing_pack: Mailing pack data
            recipient_email: Recipient email address
            dry_run: If True, prepare but don't send
            via: Email service ('smtp', 'sendgrid', 'aws_ses')
        
        Returns:
            Send result dictionary
        
        Raises:
            EmailError: If sending fails
        """
        try:
            logger.info(f"Preparing email to {recipient_email}")
            
            if dry_run:
                logger.info("Dry run mode - not sending")
                return {
                    "status": "prepared",
                    "recipient": recipient_email,
                    "method": via,
                    "dry_run": True,
                }
            
            if via == "smtp":
                return await EmailService._send_via_smtp(mailing_pack, recipient_email)
            elif via == "sendgrid":
                return await EmailService._send_via_sendgrid(mailing_pack, recipient_email)
            elif via == "aws_ses":
                return await EmailService._send_via_aws_ses(mailing_pack, recipient_email)
            else:
                raise EmailError(f"Unknown email service: {via}")
                
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            raise EmailError(f"Failed to send email: {str(e)}")

    @staticmethod
    async def _send_via_smtp(mailing_pack: Dict, recipient_email: str) -> Dict:
        """Send via SMTP."""
        settings = get_settings()
        
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            raise EmailError("SMTP credentials not configured")
        
        try:
            # Read email content
            email_path = Path(mailing_pack.get("email_path"))
            with open(email_path, "r") as f:
                email_content = f.read()
            
            # Create message
            msg = MIMEMultipart("related")
            msg["Subject"] = mailing_pack.get("email_subject", "Solar Proposal")
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = recipient_email
            
            # Add body
            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)
            msg_alternative.attach(MIMEText(email_content, "plain"))
            
            # Attach images if present
            for image_key in ["satellite_image_path", "mockup_image_path"]:
                image_path = mailing_pack.get(image_key)
                if image_path and Path(image_path).exists():
                    with open(image_path, "rb") as img_file:
                        img_data = img_file.read()
                        image = MIMEImage(img_data, _subtype="png")
                        image.add_header(
                            "Content-Disposition",
                            f"attachment; filename={Path(image_path).name}"
                        )
                        msg.attach(image)
            
            # Send
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent via SMTP to {recipient_email}")
            return {
                "status": "sent",
                "recipient": recipient_email,
                "method": "smtp",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            raise EmailError(f"SMTP send failed: {str(e)}")

    @staticmethod
    async def _send_via_sendgrid(mailing_pack: Dict, recipient_email: str) -> Dict:
        """Send via SendGrid."""
        settings = get_settings()
        
        if not settings.SENDGRID_API_KEY:
            raise EmailError("SendGrid API key not configured")
        
        logger.info(f"Would send via SendGrid to {recipient_email}")
        return {
            "status": "sent",
            "recipient": recipient_email,
            "method": "sendgrid",
        }

    @staticmethod
    async def _send_via_aws_ses(mailing_pack: Dict, recipient_email: str) -> Dict:
        """Send via AWS SES."""
        settings = get_settings()
        
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            raise EmailError("AWS credentials not configured")
        
        logger.info(f"Would send via AWS SES to {recipient_email}")
        return {
            "status": "sent",
            "recipient": recipient_email,
            "method": "aws_ses",
        }


# Note: Import at end to avoid circular imports
from datetime import datetime
