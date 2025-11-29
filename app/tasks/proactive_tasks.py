"""
Proactive analysis Celery tasks.

These tasks run periodically to analyze user data and generate suggestions.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.user import User
from app.services.ai.proactive_analysis import ProactiveAnalysisService
from app.services.google.calendar_service import GoogleCalendarService
from app.services.google.gmail_service import GoogleGmailService
from app.tasks import celery_app


@celery_app.task(name="daily_proactive_analysis")
def daily_proactive_analysis():
    """
    Daily task to analyze all users' schedules and generate proactive suggestions.

    This runs every morning at 7 AM.
    """
    asyncio.run(_run_daily_analysis())


async def _run_daily_analysis():
    """Run the daily analysis for all users."""
    async with AsyncSessionLocal() as db:
        # Get all active users
        result = await db.execute(
            select(User).where(User.is_active == True, User.google_access_token.isnot(None))  # noqa: E712
        )
        users = result.scalars().all()

        print(f"Running daily analysis for {len(users)} users...")

        for user in users:
            try:
                await _analyze_user(user, db)
            except Exception as e:
                print(f"Error analyzing user {user.id}: {e}")
                continue


async def _analyze_user(user: User, db: AsyncSession):
    """
    Analyze a single user's data and create alerts.

    Args:
        user: User to analyze
        db: Database session
    """
    print(f"Analyzing user {user.id} ({user.email})...")

    # Initialize services
    calendar_service = GoogleCalendarService(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
    )

    try:
        gmail_service = GoogleGmailService(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
        )
    except Exception:
        gmail_service = None

    # Get data for today and tomorrow
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = today_start + timedelta(days=2)

    # Fetch calendar events
    try:
        calendar_events = calendar_service.list_events(max_results=50)
        # Filter for today and tomorrow
        calendar_events = [
            event
            for event in calendar_events
            if _is_event_in_range(event, today_start, tomorrow_end)
        ]
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        calendar_events = []

    # Fetch pending tasks (from calendar - tasks are stored as special events)
    try:
        tasks = calendar_service.list_events(event_type="task", max_results=50)
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        tasks = []

    # Fetch recent emails
    emails = []
    if gmail_service:
        try:
            emails = gmail_service.list_messages(max_results=10, query="is:unread")
        except Exception as e:
            print(f"Error fetching emails: {e}")

    # Run AI analysis
    analysis_service = ProactiveAnalysisService()
    suggestions = await analysis_service.analyze_schedule(
        calendar_events=calendar_events,
        tasks=tasks,
        emails=emails,
    )

    print(f"Generated {len(suggestions)} suggestions for user {user.id}")

    # Create alerts in database
    for suggestion in suggestions:
        alert = Alert(
            user_id=user.id,
            type=suggestion.type,
            priority=suggestion.priority,
            title=suggestion.title,
            message=suggestion.message,
            context=str(suggestion.context),  # Convert dict to JSON string
            expires_at=now + timedelta(days=3),  # Alerts expire after 3 days
        )
        db.add(alert)

    await db.commit()
    print(f"Created {len(suggestions)} alerts for user {user.id}")


def _is_event_in_range(event: dict, start: datetime, end: datetime) -> bool:
    """Check if event is within date range."""
    try:
        event_start_str = event.get("start", {}).get("dateTime")
        if not event_start_str:
            return False

        event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00"))
        return start <= event_start <= end
    except Exception:
        return False


@celery_app.task(name="cleanup_old_alerts")
def cleanup_old_alerts():
    """
    Cleanup task to remove old/expired alerts.

    Runs daily at midnight.
    """
    asyncio.run(_run_cleanup())


async def _run_cleanup():
    """Run the cleanup process."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        # Delete expired alerts
        result = await db.execute(select(Alert).where(Alert.expires_at < now))
        expired_alerts = result.scalars().all()

        for alert in expired_alerts:
            await db.delete(alert)

        await db.commit()
        print(f"Cleaned up {len(expired_alerts)} expired alerts")


# Schedule configuration (to be added to Celery Beat)
celery_app.conf.beat_schedule = {
    "daily-proactive-analysis": {
        "task": "daily_proactive_analysis",
        "schedule": 3600.0 * 24,  # Every 24 hours
    },
    "cleanup-old-alerts": {
        "task": "cleanup_old_alerts",
        "schedule": 3600.0 * 24,  # Every 24 hours
    },
}
