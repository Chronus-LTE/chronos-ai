"""
Proactive Analysis Service using Gemini AI.

This service analyzes user's calendar, tasks, and emails to provide
proactive suggestions and alerts.
"""

import json
from datetime import datetime, timedelta, timezone

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.config import settings


class ProactiveSuggestion(BaseModel):
    """Model for a proactive suggestion from AI."""

    type: str = Field(..., description="Type: scheduling, overload, task_reminder, email_followup")
    priority: str = Field(..., description="Priority: high, medium, low")
    title: str = Field(..., description="Short title for the suggestion")
    message: str = Field(..., description="Detailed message explaining the suggestion")
    context: dict = Field(default_factory=dict, description="Additional context data")


class ProactiveAnalysisService:
    """Service for analyzing user data and generating proactive suggestions."""

    def __init__(self):
        """Initialize the analysis service."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )

    async def analyze_schedule(
        self,
        calendar_events: list[dict],
        tasks: list[dict],
        emails: list[dict] | None = None,
    ) -> list[ProactiveSuggestion]:
        """
        Analyze user's schedule and generate proactive suggestions.

        Args:
            calendar_events: List of calendar events (today + tomorrow)
            tasks: List of pending tasks
            emails: List of recent emails (optional)

        Returns:
            List of proactive suggestions
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(calendar_events, tasks, emails)

        # Call Gemini
        try:
            response = await self.llm.ainvoke(prompt)
            suggestions_text = response.content

            # Parse JSON response
            suggestions_data = json.loads(suggestions_text)

            # Validate and convert to Pydantic models
            suggestions = []
            for item in suggestions_data.get("suggestions", []):
                try:
                    suggestion = ProactiveSuggestion(**item)
                    suggestions.append(suggestion)
                except Exception as e:
                    print(f"Failed to parse suggestion: {e}")
                    continue

            return suggestions

        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return []

    def _build_analysis_prompt(
        self,
        calendar_events: list[dict],
        tasks: list[dict],
        emails: list[dict] | None = None,
    ) -> str:
        """Build the analysis prompt for Gemini."""
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = f"""You are an AI assistant analyzing a user's schedule to provide proactive suggestions.

Current Date: {today}
Analysis Period: Today ({today}) and Tomorrow ({tomorrow})

**CALENDAR EVENTS:**
{json.dumps(calendar_events, indent=2) if calendar_events else "No events scheduled"}

**PENDING TASKS:**
{json.dumps(tasks, indent=2) if tasks else "No pending tasks"}

**RECENT EMAILS:**
{json.dumps(emails[:5], indent=2) if emails else "No recent emails"}

**YOUR TASK:**
Analyze the above data and provide proactive suggestions based on these scenarios:

1. **Schedule Gaps (type: "scheduling")**
   - Find gaps ≥ 90 minutes in the schedule
   - Suggest productive activities for those gaps
   - Priority: medium

2. **Overload Warning (type: "overload")**
   - Detect days with too many meetings (≥ 5) or tasks
   - Suggest rescheduling non-urgent items
   - Priority: high

3. **Task Reminders (type: "task_reminder")**
   - Find important tasks that are:
     * Overdue by 24+ hours
     * Due within next 24 hours
   - Suggest immediate action
   - Priority: high for overdue, medium for upcoming

4. **Email Follow-up (type: "email_followup")**
   - Find important unread emails older than 2 days
   - Suggest responding or taking action
   - Priority: medium

**OUTPUT FORMAT:**
Return ONLY a valid JSON object with this exact structure:
{{
  "suggestions": [
    {{
      "type": "scheduling|overload|task_reminder|email_followup",
      "priority": "high|medium|low",
      "title": "Short title (max 60 chars)",
      "message": "Detailed explanation of the suggestion",
      "context": {{
        "event_ids": ["id1", "id2"],
        "task_ids": ["id1"],
        "date": "2024-01-01",
        "time_slot": "14:00-16:00"
      }}
    }}
  ]
}}

**IMPORTANT RULES:**
- Return valid JSON only, no markdown or extra text
- Maximum 5 suggestions
- Be specific and actionable
- Use friendly, helpful tone
- Include relevant IDs in context for tracking
- If no suggestions needed, return: {{"suggestions": []}}

Generate suggestions now:"""

        return prompt

    def detect_schedule_gaps(self, calendar_events: list[dict]) -> list[dict]:
        """
        Detect gaps in schedule (≥ 90 minutes).

        Args:
            calendar_events: List of calendar events

        Returns:
            List of gaps with start/end times
        """
        if not calendar_events:
            return []

        # Sort events by start time
        sorted_events = sorted(
            calendar_events,
            key=lambda x: datetime.fromisoformat(x.get("start", {}).get("dateTime", "")),
        )

        gaps = []
        for i in range(len(sorted_events) - 1):
            current_end = datetime.fromisoformat(
                sorted_events[i].get("end", {}).get("dateTime", "")
            )
            next_start = datetime.fromisoformat(
                sorted_events[i + 1].get("start", {}).get("dateTime", "")
            )

            gap_duration = (next_start - current_end).total_seconds() / 60  # minutes

            if gap_duration >= 90:
                gaps.append(
                    {
                        "start": current_end.isoformat(),
                        "end": next_start.isoformat(),
                        "duration_minutes": int(gap_duration),
                    }
                )

        return gaps

    def detect_overload(self, calendar_events: list[dict], tasks: list[dict], date: str) -> bool:
        """
        Detect if a specific date is overloaded.

        Args:
            calendar_events: List of calendar events
            tasks: List of tasks
            date: Date to check (YYYY-MM-DD)

        Returns:
            True if overloaded, False otherwise
        """
        # Count events on that date
        events_count = sum(
            1
            for event in calendar_events
            if event.get("start", {}).get("dateTime", "").startswith(date)
        )

        # Count tasks due on that date
        tasks_count = sum(1 for task in tasks if task.get("due", "").startswith(date))

        # Overload criteria: ≥ 5 events OR ≥ 8 tasks OR combined ≥ 10
        return events_count >= 5 or tasks_count >= 8 or (events_count + tasks_count) >= 10

    def find_overdue_tasks(self, tasks: list[dict]) -> list[dict]:
        """
        Find tasks that are overdue by 24+ hours.

        Args:
            tasks: List of tasks

        Returns:
            List of overdue tasks
        """
        now = datetime.now(timezone.utc)
        overdue = []

        for task in tasks:
            due_str = task.get("due")
            if not due_str:
                continue

            try:
                due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                hours_overdue = (now - due_date).total_seconds() / 3600

                if hours_overdue >= 24:
                    task["hours_overdue"] = int(hours_overdue)
                    overdue.append(task)
            except Exception:
                continue

        return overdue

    def find_upcoming_tasks(self, tasks: list[dict], hours: int = 24) -> list[dict]:
        """
        Find tasks due within next X hours.

        Args:
            tasks: List of tasks
            hours: Number of hours to look ahead

        Returns:
            List of upcoming tasks
        """
        now = datetime.now(timezone.utc)
        upcoming = []

        for task in tasks:
            due_str = task.get("due")
            if not due_str:
                continue

            try:
                due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                hours_until = (due_date - now).total_seconds() / 3600

                if 0 <= hours_until <= hours:
                    task["hours_until_due"] = int(hours_until)
                    upcoming.append(task)
            except Exception:
                continue

        return upcoming
