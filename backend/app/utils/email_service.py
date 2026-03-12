"""Async email sending via Gmail SMTP."""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.utils.config import settings

logger = logging.getLogger(__name__)

_VERIFY_HTML = """\
<html><body style="font-family:Arial,sans-serif;max-width:480px;margin:auto">
  <h2 style="color:#1a56db">Verify your email</h2>
  <p>Welcome to <strong>AI Detection Platform</strong>!</p>
  <p>Your verification code is:</p>
  <div style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1a56db;
              background:#f0f4ff;padding:16px;text-align:center;border-radius:8px">
    {otp}
  </div>
  <p style="color:#666">Expires in <strong>{expiry}</strong> minutes. Do not share this code.</p>
</body></html>"""

_2FA_HTML = """\
<html><body style="font-family:Arial,sans-serif;max-width:480px;margin:auto">
  <h2 style="color:#1a56db">Two-Factor Authentication</h2>
  <p>Your 2FA code is:</p>
  <div style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1a56db;
              background:#f0f4ff;padding:16px;text-align:center;border-radius:8px">
    {otp}
  </div>
  <p style="color:#666">Expires in <strong>{expiry}</strong> minutes. Never share this code.</p>
</body></html>"""


class EmailService:
    """Sends transactional emails via Gmail SMTP using TLS."""

    async def _send(self, to: str, subject: str, html: str, plain: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SENDER_EMAIL}>"
        msg["To"] = to
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            logger.info("Email sent", extra={"to": to, "subject": subject})
            return True
        except Exception as exc:
            logger.error("Email send failed", extra={"to": to, "error": str(exc)})
            return False

    async def send_verification_email(self, email: str, otp: str) -> bool:
        """Send email-verification OTP."""
        html = _VERIFY_HTML.format(otp=otp, expiry=settings.OTP_EXPIRY_MINUTES)
        plain = f"Your verification code: {otp}  (expires in {settings.OTP_EXPIRY_MINUTES} min)"
        return await self._send(email, "Verify your email – AI Detection Platform", html, plain)

    async def send_2fa_email(self, email: str, otp: str) -> bool:
        """Send 2FA OTP."""
        html = _2FA_HTML.format(otp=otp, expiry=settings.OTP_EXPIRY_MINUTES)
        plain = f"Your 2FA code: {otp}  (expires in {settings.OTP_EXPIRY_MINUTES} min)"
        return await self._send(email, "Your 2FA code – AI Detection Platform", html, plain)


email_service = EmailService()
