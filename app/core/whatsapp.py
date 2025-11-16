"""
WhatsApp Integration for Phone Verification

Implements phone number verification via WhatsApp messages
"""
import httpx
from typing import Optional
from app.core.config import settings
from app.core.security import generate_verification_code, sanitize_phone_number, validate_phone_format
from app.core.redis_client import redis_client
import asyncio


class WhatsAppClient:
    """WhatsApp API client for sending verification codes"""

    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.api_key = settings.WHATSAPP_API_KEY

    async def send_verification_code(
        self,
        phone: str,
        language: str = "ru"
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Send verification code via WhatsApp

        Args:
            phone: Phone number in E.164 format
            language: Message language (ru, kk, en)

        Returns:
            (success, code, error_message)
        """
        # Validate and sanitize phone number
        phone = sanitize_phone_number(phone)
        if not validate_phone_format(phone):
            return False, None, "Invalid phone number format"

        # Check rate limiting for this phone number
        attempts = redis_client.get_login_attempts(f"phone_verification:{phone}")
        if attempts >= 3:
            return False, None, "Too many verification requests. Please try again later."

        # Generate verification code
        code = generate_verification_code()

        # Store code in Redis
        if not redis_client.store_verification_code(phone, code):
            return False, None, "Failed to store verification code"

        # Get message template based on language
        message = self._get_message_template(code, language)

        # Send WhatsApp message
        success, error = await self._send_message(phone, message)

        if success:
            # Increment rate limit counter
            redis_client.increment_login_attempts(f"phone_verification:{phone}")
            return True, code, None
        else:
            # Clean up stored code on failure
            redis_client.delete_verification_code(phone)
            return False, None, error

    async def _send_message(self, phone: str, message: str) -> tuple[bool, Optional[str]]:
        """
        Send WhatsApp message via API

        Args:
            phone: Recipient phone number
            message: Message text

        Returns:
            (success, error_message)
        """
        if not self.api_key:
            # For development: just log and return success
            print(f"📱 [DEV MODE] WhatsApp verification code for {phone}: {message}")
            return True, None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/messages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "to": phone,
                        "type": "text",
                        "text": {"body": message}
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    return True, None
                else:
                    error_msg = f"WhatsApp API error: {response.status_code}"
                    print(f"❌ {error_msg}")
                    return False, error_msg

        except httpx.TimeoutException:
            error_msg = "WhatsApp API timeout"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to send WhatsApp message: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def _get_message_template(self, code: str, language: str) -> str:
        """Get localized message template"""
        templates = {
            "ru": f"""Ваш код подтверждения Jazyl: {code}

Код действителен 5 минут.
Никому не сообщайте этот код!

Не запрашивали код? Проигнорируйте это сообщение.""",

            "kk": f"""Jazyl растау коды: {code}

Код 5 минут жарамды.
Бұл кодты ешкімге айтпаңыз!

Код сұрамадыңыз ба? Бұл хабарды елемеңіз.""",

            "en": f"""Your Jazyl verification code: {code}

Code is valid for 5 minutes.
Never share this code with anyone!

Didn't request a code? Ignore this message."""
        }

        return templates.get(language, templates["ru"])

    async def send_booking_confirmation(
        self,
        phone: str,
        salon_name: str,
        master_name: str,
        service_name: str,
        booking_date: str,
        booking_time: str,
        language: str = "ru"
    ) -> tuple[bool, Optional[str]]:
        """Send booking confirmation message"""
        templates = {
            "ru": f"""✅ Запись подтверждена!

Салон: {salon_name}
Мастер: {master_name}
Услуга: {service_name}
Дата: {booking_date}
Время: {booking_time}

Ждем вас! 💇‍♀️""",

            "kk": f"""✅ Жазылу расталды!

Салон: {salon_name}
Шебер: {master_name}
Қызмет: {service_name}
Күні: {booking_date}
Уақыты: {booking_time}

Сізді күтеміз! 💇‍♀️""",

            "en": f"""✅ Booking confirmed!

Salon: {salon_name}
Master: {master_name}
Service: {service_name}
Date: {booking_date}
Time: {booking_time}

See you there! 💇‍♀️"""
        }

        message = templates.get(language, templates["ru"])
        success, error = await self._send_message(phone, message)
        return success, error

    async def send_booking_reminder(
        self,
        phone: str,
        salon_name: str,
        booking_time: str,
        hours_before: int = 24,
        language: str = "ru"
    ) -> tuple[bool, Optional[str]]:
        """Send booking reminder"""
        templates = {
            "ru": f"""⏰ Напоминание о записи

{salon_name}
Через {hours_before} часов в {booking_time}

До встречи! 💇‍♀️""",

            "kk": f"""⏰ Жазылу туралы еске салу

{salon_name}
{hours_before} сағаттан кейін {booking_time}

Кездескенше! 💇‍♀️""",

            "en": f"""⏰ Booking reminder

{salon_name}
In {hours_before} hours at {booking_time}

See you soon! 💇‍♀️"""
        }

        message = templates.get(language, templates["ru"])
        success, error = await self._send_message(phone, message)
        return success, error


# Global WhatsApp client instance
whatsapp_client = WhatsAppClient()
