"""
Google Gmail tools for the AI Agent.
"""

import contextlib
import traceback

from langchain.tools import Tool

from app.services.google.gmail_service import GoogleGmailService
from app.services.tools.base import BaseToolSet


class GoogleGmailToolSet(BaseToolSet):
    """Tool set for Gmail operations."""

    def __init__(self, user_token: str):
        super().__init__(user_token)
        self.gmail_service = GoogleGmailService(token=user_token)

    def get_tools(self) -> list[Tool]:
        """Get Gmail tools."""
        return [
            Tool(
                name="list_emails",
                func=self._list_emails,
                description="Use this to list recent emails. Input can be empty string or a number for max results (default 10).",
            ),
            Tool(
                name="search_emails",
                func=self._search_emails,
                description="Use this to search emails using Gmail search syntax. Input should be the search query. Examples: 'is:unread', 'from:example@gmail.com', 'subject:meeting', 'has:attachment'",
            ),
            Tool(
                name="read_email",
                func=self._read_email,
                description="Use this to read a specific email by ID. Input should be the email ID.",
            ),
            Tool(
                name="send_email",
                func=self._send_email,
                description="Use this to send an email. Input should be 'recipient@email.com | Subject | Body'",
            ),
            Tool(
                name="mark_email_as_read",
                func=self._mark_as_read,
                description="Use this to mark an email as read. Input should be the email ID.",
            ),
            Tool(
                name="mark_email_as_unread",
                func=self._mark_as_unread,
                description="Use this to mark an email as unread. Input should be the email ID.",
            ),
            Tool(
                name="get_unread_count",
                func=self._get_unread_count,
                description="Use this to get the count of unread emails. Input can be empty string.",
            ),
        ]

    def _list_emails(self, input_str: str | list) -> str:
        """List recent emails."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = str(input_str[0]) if input_str else ""

            max_results = 10
            if input_str and input_str.strip():
                with contextlib.suppress(ValueError):
                    max_results = int(input_str.strip())
            messages = self.gmail_service.list_messages(max_results=max_results)

            if not messages:
                return "📭 No emails found."

            result = f"📧 Recent Emails ({len(messages)}):\n\n"
            for msg in messages:
                unread_icon = "🔵" if msg["isUnread"] else "⚪"
                result += f"{unread_icon} **{msg['subject']}**\n"
                result += f"   From: {msg['from']}\n"
                result += f"   Date: {msg['date']}\n"
                result += f"   Preview: {msg['snippet'][:100]}...\n"
                result += f"   ID: {msg['id']}\n\n"

            return result

        except Exception as e:
            traceback.print_exc()
            return f"Error listing emails: {e!s}"

    def _search_emails(self, input_str: str | list) -> str:
        """Search emails using Gmail search syntax."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = " ".join(str(item) for item in input_str)

            query = input_str.strip()
            if not query:
                return "ERROR: Please provide a search query. Examples: 'is:unread', 'from:example@gmail.com', 'subject:meeting'"

            messages = self.gmail_service.search_messages(query=query)

            if not messages:
                return f"📭 No emails found matching: '{query}'"

            result = f"🔍 Search Results for '{query}' ({len(messages)}):\n\n"
            for msg in messages:
                unread_icon = "🔵" if msg["isUnread"] else "⚪"
                result += f"{unread_icon} **{msg['subject']}**\n"
                result += f"   From: {msg['from']}\n"
                result += f"   Date: {msg['date']}\n"
                result += f"   Preview: {msg['snippet'][:100]}...\n"
                result += f"   ID: {msg['id']}\n\n"

            return result

        except Exception as e:
            traceback.print_exc()
            return f"Error searching emails: {e!s}"

    def _read_email(self, input_str: str | list) -> str:
        """Read a specific email by ID."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = str(input_str[0]) if input_str else ""

            message_id = input_str.strip()
            if not message_id:
                return "ERROR: Please provide an email ID."

            msg = self.gmail_service.get_message(message_id)

            unread_icon = "🔵" if msg["isUnread"] else "⚪"
            result = f"{unread_icon} **Email Details**\n\n"
            result += f"**Subject:** {msg['subject']}\n"
            result += f"**From:** {msg['from']}\n"
            result += f"**To:** {msg['to']}\n"
            result += f"**Date:** {msg['date']}\n"
            result += f"**ID:** {msg['id']}\n\n"
            result += "**Body:**\n"
            result += f"{msg['body'][:1000]}"  # Limit body to 1000 chars

            if len(msg["body"]) > 1000:
                result += "\n\n... (email truncated)"

            return result

        except Exception as e:
            traceback.print_exc()
            return f"Error reading email: {e!s}"

    def _send_email(self, input_str: str | list) -> str:
        """Send an email."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = " | ".join(str(item) for item in input_str)

            parts = [p.strip() for p in input_str.split("|")]

            if len(parts) < 3:
                return "ERROR: Missing required information. Please provide: recipient@email.com | Subject | Body"

            to_email = parts[0]
            subject = parts[1]
            body = parts[2]

            if not to_email or "@" not in to_email:
                return "ERROR: Invalid recipient email address."

            if not subject:
                return "ERROR: Subject cannot be empty."

            if not body:
                return "ERROR: Body cannot be empty."

            result = self.gmail_service.send_message(
                to=to_email,
                subject=subject,
                body=body,
            )

            return (
                f"✅ Email sent successfully to {to_email}\nMessage ID: {result.get('id', 'N/A')}"
            )

        except Exception as e:
            traceback.print_exc()
            return f"Error sending email: {e!s}"

    def _mark_as_read(self, input_str: str | list) -> str:
        """Mark an email as read."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = str(input_str[0]) if input_str else ""

            message_id = input_str.strip()
            if not message_id:
                return "ERROR: Please provide an email ID."

            self.gmail_service.mark_as_read(message_id)
            return f"✅ Email marked as read: {message_id}"

        except Exception as e:
            traceback.print_exc()
            return f"Error marking email as read: {e!s}"

    def _mark_as_unread(self, input_str: str | list) -> str:
        """Mark an email as unread."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = str(input_str[0]) if input_str else ""

            message_id = input_str.strip()
            if not message_id:
                return "ERROR: Please provide an email ID."

            self.gmail_service.mark_as_unread(message_id)
            return f"✅ Email marked as unread: {message_id}"

        except Exception as e:
            traceback.print_exc()
            return f"Error marking email as unread: {e!s}"

    def _get_unread_count(self, input_str: str | list) -> str:
        """Get count of unread emails."""
        try:
            count = self.gmail_service.get_unread_count()
            return f"📬 You have {count} unread email(s)."

        except Exception as e:
            traceback.print_exc()
            return f"Error getting unread count: {e!s}"
