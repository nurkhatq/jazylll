"""
Background Tasks Service for Automated Booking Operations

Handles:
- Automated reminders (24h and 1h before booking)
- Automated review requests after completed bookings
- Booking status updates
- Statistics calculations
"""
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.salon import Master
from app.core.whatsapp import whatsapp_client
import asyncio


async def send_booking_reminders():
    """
    Send automated reminders for upcoming bookings
    - 24 hours before: First reminder
    - 1 hour before: Final reminder

    Should be called by Celery/scheduler every 15 minutes
    """
    db = SessionLocal()
    try:
        now = datetime.now()

        # Calculate reminder times
        reminder_24h_start = now + timedelta(hours=23, minutes=45)
        reminder_24h_end = now + timedelta(hours=24, minutes=15)

        reminder_1h_start = now + timedelta(hours=0, minutes=45)
        reminder_1h_end = now + timedelta(hours=1, minutes=15)

        # Get bookings needing 24h reminder
        bookings_24h = db.query(Booking).join(Booking.client).filter(
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.reminded_at.is_(None),
            Booking.booking_date >= reminder_24h_start.date(),
            Booking.booking_date <= reminder_24h_end.date()
        ).all()

        # Get bookings needing 1h reminder
        today = now.date()
        bookings_1h = db.query(Booking).join(Booking.client).filter(
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.reminded_at.is_not(None),  # Already got 24h reminder
            Booking.booking_date == today,
            Booking.start_time >= reminder_1h_start.time(),
            Booking.start_time <= reminder_1h_end.time()
        ).all()

        print(f"📅 Found {len(bookings_24h)} bookings for 24h reminder")
        print(f"📅 Found {len(bookings_1h)} bookings for 1h reminder")

        # Send 24h reminders
        for booking in bookings_24h:
            await send_24h_reminder(booking, db)

        # Send 1h reminders
        for booking in bookings_1h:
            await send_1h_reminder(booking, db)

    except Exception as e:
        print(f"❌ Error in send_booking_reminders: {e}")
    finally:
        db.close()


async def send_24h_reminder(booking: Booking, db: Session):
    """Send 24-hour reminder"""
    try:
        if not booking.client or not booking.client.phone:
            return

        master_name = "Master"
        salon_name = "Salon"

        if booking.master and booking.master.user:
            master_name = f"{booking.master.user.first_name or ''} {booking.master.user.last_name or ''}".strip()

        if booking.master and booking.master.salon:
            salon_name = booking.master.salon.display_name

        success, error = await whatsapp_client.send_booking_reminder(
            phone=booking.client.phone,
            salon_name=salon_name,
            booking_time=booking.start_time.strftime("%H:%M"),
            hours_before=24,
            language="ru"
        )

        if success:
            booking.reminded_at = datetime.now()
            db.commit()
            print(f"✅ Sent 24h reminder for booking {booking.id}")
        else:
            print(f"❌ Failed to send 24h reminder for booking {booking.id}: {error}")

    except Exception as e:
        print(f"❌ Error sending 24h reminder for booking {booking.id}: {e}")


async def send_1h_reminder(booking: Booking, db: Session):
    """Send 1-hour reminder"""
    try:
        if not booking.client or not booking.client.phone:
            return

        master_name = "Master"
        salon_name = "Salon"

        if booking.master and booking.master.user:
            master_name = f"{booking.master.user.first_name or ''} {booking.master.user.last_name or ''}".strip()

        if booking.master and booking.master.salon:
            salon_name = booking.master.salon.display_name

        success, error = await whatsapp_client.send_booking_reminder(
            phone=booking.client.phone,
            salon_name=salon_name,
            booking_time=booking.start_time.strftime("%H:%M"),
            hours_before=1,
            language="ru"
        )

        if success:
            print(f"✅ Sent 1h reminder for booking {booking.id}")
        else:
            print(f"❌ Failed to send 1h reminder for booking {booking.id}: {error}")

    except Exception as e:
        print(f"❌ Error sending 1h reminder for booking {booking.id}: {e}")


async def request_reviews_for_completed_bookings():
    """
    Send review requests for completed bookings
    - Sends 2 hours after booking completion
    - Only if no review exists yet

    Should be called by Celery/scheduler every 30 minutes
    """
    db = SessionLocal()
    try:
        # Get bookings completed 2+ hours ago without reviews
        cutoff_time = datetime.now() - timedelta(hours=2)

        # Import Review model
        from app.models.booking import Review

        completed_bookings = db.query(Booking).outerjoin(Review).filter(
            Booking.status == BookingStatus.COMPLETED,
            Booking.completed_at <= cutoff_time,
            Booking.completed_at >= datetime.now() - timedelta(days=7),  # Within last week
            Review.id.is_(None)  # No review yet
        ).all()

        print(f"📝 Found {len(completed_bookings)} bookings ready for review request")

        for booking in completed_bookings:
            await send_review_request(booking, db)

    except Exception as e:
        print(f"❌ Error in request_reviews_for_completed_bookings: {e}")
    finally:
        db.close()


async def send_review_request(booking: Booking, db: Session):
    """Send review request via WhatsApp"""
    try:
        if not booking.client or not booking.client.phone:
            return

        salon_name = "Salon"
        if booking.master and booking.master.salon:
            salon_name = booking.master.salon.display_name

        # Create message
        message = f"""Здравствуйте! 👋

Вы посетили {salon_name}.

Пожалуйста, оцените наш сервис! ⭐
Ваше мнение важно для нас.

Оставьте отзыв в приложении Jazyl.

Спасибо! 💇‍♀️"""

        from app.core.whatsapp import whatsapp_client
        success, error = await whatsapp_client._send_message(
            phone=booking.client.phone,
            message=message
        )

        if success:
            print(f"✅ Sent review request for booking {booking.id}")
        else:
            print(f"❌ Failed to send review request for booking {booking.id}: {error}")

    except Exception as e:
        print(f"❌ Error sending review request for booking {booking.id}: {e}")


async def auto_complete_bookings():
    """
    Automatically mark bookings as completed
    - 2 hours after end_time if still IN_PROGRESS or CONFIRMED

    Should be called by Celery/scheduler every hour
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        cutoff_time = now - timedelta(hours=2)
        today = now.date()
        yesterday = today - timedelta(days=1)

        # Get bookings to auto-complete
        bookings_to_complete = db.query(Booking).filter(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]),
            Booking.booking_date.in_([today, yesterday]),
        ).all()

        completed_count = 0
        for booking in bookings_to_complete:
            booking_end_datetime = datetime.combine(booking.booking_date, booking.end_time)
            if booking_end_datetime + timedelta(hours=2) <= now:
                booking.status = BookingStatus.COMPLETED
                booking.completed_at = booking_end_datetime
                completed_count += 1

        if completed_count > 0:
            db.commit()
            print(f"✅ Auto-completed {completed_count} bookings")

    except Exception as e:
        print(f"❌ Error in auto_complete_bookings: {e}")
        db.rollback()
    finally:
        db.close()


async def mark_no_shows():
    """
    Mark bookings as NO_SHOW
    - 30 minutes after start_time if still CONFIRMED

    Should be called by Celery/scheduler every 30 minutes
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=30)
        today = now.date()

        # Get bookings to mark as no-show
        bookings_to_mark = db.query(Booking).filter(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.booking_date == today,
        ).all()

        no_show_count = 0
        for booking in bookings_to_mark:
            booking_start_datetime = datetime.combine(booking.booking_date, booking.start_time)
            if booking_start_datetime + timedelta(minutes=30) <= now:
                booking.status = BookingStatus.NO_SHOW
                no_show_count += 1

        if no_show_count > 0:
            db.commit()
            print(f"⚠️  Marked {no_show_count} bookings as NO_SHOW")

    except Exception as e:
        print(f"❌ Error in mark_no_shows: {e}")
        db.rollback()
    finally:
        db.close()


# Celery tasks configuration
"""
To use with Celery, add to your celery_app.py:

from celery import Celery
from celery.schedules import crontab
from app.core.booking_tasks import (
    send_booking_reminders,
    request_reviews_for_completed_bookings,
    auto_complete_bookings,
    mark_no_shows
)

celery_app = Celery('jazyl', broker='redis://localhost:6379/0')

celery_app.conf.beat_schedule = {
    'send-reminders-every-15-min': {
        'task': 'app.core.booking_tasks.send_booking_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'request-reviews-every-30-min': {
        'task': 'app.core.booking_tasks.request_reviews_for_completed_bookings',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'auto-complete-bookings-hourly': {
        'task': 'app.core.booking_tasks.auto_complete_bookings',
        'schedule': crontab(minute=0),  # Every hour
    },
    'mark-no-shows-every-30-min': {
        'task': 'app.core.booking_tasks.mark_no_shows',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
"""
