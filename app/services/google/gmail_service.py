"""
Google Gmail Service for managing emails.
"""

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings


class GoogleGmailService:
    """Service for interacting with Gmail API."""

    def __init__(self, token: str, refresh_token: str | None = None):
        """
        Initialize Gmail service with user credentials.

        Args:
            token: Access token
            refresh_token: Refresh token (optional)
        """
        self.credentials = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        self.service = build("gmail", "v1", credentials=self.credentials)

    def list_messages(
        self,
        max_results: int = 20,
        query: str = "",
        label_ids: list[str] | None = None,
    ):
        """
        List messages in user's mailbox.

        Args:
            max_results: Maximum number of messages to return
            query: Gmail search query (e.g., "is:unread", "from:example@gmail.com")
            label_ids: List of label IDs to filter by (e.g., ["INBOX", "UNREAD"])

        Returns:
            List of message objects with basic info
        """
        try:
            params = {
                "userId": "me",
                "maxResults": max_results,
            }

            if query:
                params["q"] = query

            if label_ids:
                params["labelIds"] = label_ids

            results = self.service.users().messages().list(**params).execute()
            messages = results.get("messages", [])

            # Get full message details for each message
            detailed_messages = []
            for msg in messages:
                detailed_msg = self.get_message(msg["id"])
                detailed_messages.append(detailed_msg)

            return detailed_messages

        except Exception as e:
            msg = f"Failed to list messages: {e!s}"
            raise RuntimeError(msg) from e

    def get_message(self, message_id: str):
        """
        Get a specific message by ID.

        Args:
            message_id: Message ID

        Returns:
            Message object with full details
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            # Parse message details
            headers = message.get("payload", {}).get("headers", [])

            def get_header(name):
                return next(
                    (h["value"] for h in headers if h["name"].lower() == name.lower()), None
                )

            subject = get_header("Subject") or "No Subject"
            from_email = get_header("From") or "Unknown"
            to_email = get_header("To") or "Unknown"
            cc_email = get_header("Cc")
            bcc_email = get_header("Bcc")
            date = get_header("Date") or "Unknown"

            # Get message body
            body = self._get_message_body(message)

            # Get labels
            labels = message.get("labelIds", [])

            return {
                "id": message["id"],
                "threadId": message["threadId"],
                "subject": subject,
                "from": from_email,
                "to": to_email,
                "cc": cc_email,
                "bcc": bcc_email,
                "date": date,
                "snippet": message.get("snippet", ""),
                "body": body,
                "labels": labels,
                "isUnread": "UNREAD" in labels,
            }

        except Exception as e:
            msg = f"Failed to get message {message_id}: {e!s}"
            raise RuntimeError(msg) from e

    def _get_message_body(self, message: dict) -> str:
        """
        Extract message body from Gmail message object.

        Args:
            message: Gmail message object

        Returns:
            Message body as string
        """
        try:
            payload = message.get("payload", {})

            # Try to get body from parts
            if "parts" in payload:
                parts = payload["parts"]
                for part in parts:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8")

                    # Check nested parts
                    if "parts" in part:
                        for nested_part in part["parts"]:
                            if nested_part.get("mimeType") == "text/plain":
                                data = nested_part.get("body", {}).get("data", "")
                                if data:
                                    return base64.urlsafe_b64decode(data).decode("utf-8")

            # Try to get body directly
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8")

            return ""

        except Exception:
            return ""

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
    ):
        """
        Send an email message.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (optional, defaults to authenticated user)

        Returns:
            Sent message object
        """
        try:
            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject

            if from_email:
                message["from"] = from_email

            msg = MIMEText(body)
            message.attach(msg)

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {"raw": raw}

            return self.service.users().messages().send(userId="me", body=send_message).execute()

        except Exception as e:
            msg = f"Failed to send message: {e!s}"
            raise RuntimeError(msg) from e

    def mark_as_read(self, message_id: str):
        """
        Mark a message as read.

        Args:
            message_id: Message ID

        Returns:
            Updated message object
        """
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to mark message as read: {e!s}"
            raise RuntimeError(msg) from e

    def mark_as_unread(self, message_id: str):
        """
        Mark a message as unread.

        Args:
            message_id: Message ID

        Returns:
            Updated message object
        """
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to mark message as unread: {e!s}"
            raise RuntimeError(msg) from e

    def delete_message(self, message_id: str):
        """
        Delete a message (move to trash).

        Args:
            message_id: Message ID

        Returns:
            None
        """
        try:
            self.service.users().messages().trash(userId="me", id=message_id).execute()
        except Exception as e:
            msg = f"Failed to delete message: {e!s}"
            raise RuntimeError(msg) from e

    def search_messages(self, query: str, max_results: int = 20):
        """
        Search messages using Gmail search syntax.

        Args:
            query: Gmail search query
                Examples:
                - "is:unread" - unread messages
                - "from:example@gmail.com" - from specific sender
                - "subject:meeting" - subject contains "meeting"
                - "has:attachment" - has attachments
                - "after:2024/01/01" - after specific date
            max_results: Maximum number of results

        Returns:
            List of matching messages
        """
        return self.list_messages(max_results=max_results, query=query)

    def get_labels(self):
        """
        Get all labels in user's mailbox.

        Returns:
            List of label objects
        """
        try:
            results = self.service.users().labels().list(userId="me").execute()
            return results.get("labels", [])
        except Exception as e:
            msg = f"Failed to get labels: {e!s}"
            raise RuntimeError(msg) from e

    def get_unread_count(self):
        """
        Get count of unread messages.

        Returns:
            Number of unread messages
        """
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", labelIds=["UNREAD"], maxResults=1)
                .execute()
            )
            return results.get("resultSizeEstimate", 0)
        except Exception as e:
            msg = f"Failed to get unread count: {e!s}"
            raise RuntimeError(msg) from e

    # DRAFT MANAGEMENT (like Notion/Lark)

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
        cc: str | None = None,
        bcc: str | None = None,
        html_body: str | None = None,
    ):
        """
        Create an email draft (not sent yet).

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            html_body: HTML version of body (optional)

        Returns:
            Draft object with ID
        """
        try:
            message = MIMEMultipart("alternative") if html_body else MIMEMultipart()
            message["to"] = to
            message["subject"] = subject

            if from_email:
                message["from"] = from_email
            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc

            # Add plain text
            message.attach(MIMEText(body, "plain"))

            # Add HTML if provided
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            draft = {"message": {"raw": raw}}

            result = self.service.users().drafts().create(userId="me", body=draft).execute()

            return {
                "id": result["id"],
                "message_id": result["message"]["id"],
                "to": to,
                "subject": subject,
                "body": body,
            }

        except Exception as e:
            msg = f"Failed to create draft: {e!s}"
            raise RuntimeError(msg) from e

    def list_drafts(self, max_results: int = 20):
        """
        List all drafts.

        Args:
            max_results: Maximum number of drafts to return

        Returns:
            List of draft objects
        """
        try:
            results = (
                self.service.users().drafts().list(userId="me", maxResults=max_results).execute()
            )
            drafts = results.get("drafts", [])

            detailed_drafts = []
            for draft in drafts:
                draft_detail = self.get_draft(draft["id"])
                detailed_drafts.append(draft_detail)

            return detailed_drafts

        except Exception as e:
            msg = f"Failed to list drafts: {e!s}"
            raise RuntimeError(msg) from e

    def get_draft(self, draft_id: str):
        """
        Get a specific draft by ID.

        Args:
            draft_id: Draft ID

        Returns:
            Draft object with details
        """
        try:
            draft = self.service.users().drafts().get(userId="me", id=draft_id).execute()

            message = draft["message"]
            headers = message.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            to_email = next((h["value"] for h in headers if h["name"] == "To"), "Unknown")

            return {
                "id": draft["id"],
                "message_id": message["id"],
                "subject": subject,
                "to": to_email,
                "snippet": message.get("snippet", ""),
            }

        except Exception as e:
            msg = f"Failed to get draft {draft_id}: {e!s}"
            raise RuntimeError(msg) from e

    def send_draft(self, draft_id: str):
        """
        Send a draft email.

        Args:
            draft_id: Draft ID to send

        Returns:
            Sent message object
        """
        try:
            return self.service.users().drafts().send(userId="me", body={"id": draft_id}).execute()

        except Exception as e:
            msg = f"Failed to send draft: {e!s}"
            raise RuntimeError(msg) from e

    def update_draft(self, draft_id: str, to: str, subject: str, body: str):
        """
        Update an existing draft.

        Args:
            draft_id: Draft ID to update
            to: New recipient
            subject: New subject
            body: New body

        Returns:
            Updated draft object
        """
        try:
            # Delete old draft and create new one
            self.delete_draft(draft_id)
            return self.create_draft(to=to, subject=subject, body=body)

        except Exception as e:
            msg = f"Failed to update draft: {e!s}"
            raise RuntimeError(msg) from e

    def delete_draft(self, draft_id: str):
        """
        Delete a draft.

        Args:
            draft_id: Draft ID to delete

        Returns:
            None
        """
        try:
            self.service.users().drafts().delete(userId="me", id=draft_id).execute()
        except Exception as e:
            msg = f"Failed to delete draft: {e!s}"
            raise RuntimeError(msg) from e

    # THREADING & CONVERSATION (like Notion/Lark)

    def get_thread(self, thread_id: str):
        """
        Get all messages in a thread/conversation.

        Args:
            thread_id: Thread ID

        Returns:
            Thread object with all messages
        """
        try:
            thread = (
                self.service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )

            messages = []
            for msg in thread.get("messages", []):
                headers = msg.get("payload", {}).get("headers", [])
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"), "No Subject"
                )
                from_email = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

                messages.append(
                    {
                        "id": msg["id"],
                        "subject": subject,
                        "from": from_email,
                        "date": date,
                        "snippet": msg.get("snippet", ""),
                        "body": self._get_message_body(msg),
                    }
                )

            return {
                "id": thread["id"],
                "snippet": thread.get("snippet", ""),
                "messages": messages,
                "message_count": len(messages),
            }

        except Exception as e:
            msg = f"Failed to get thread: {e!s}"
            raise RuntimeError(msg) from e

    def reply_to_thread(self, thread_id: str, body: str):
        """
        Reply to an email thread.

        Args:
            thread_id: Thread ID to reply to
            body: Reply body

        Returns:
            Sent message object
        """
        try:
            # Get original thread to extract subject and recipient
            thread = self.get_thread(thread_id)
            if not thread["messages"]:
                msg = "Thread has no messages"
                raise ValueError(msg)

            original = thread["messages"][0]
            subject = original["subject"]
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"

            # Extract recipient from original sender
            from_email = original["from"]

            message = MIMEMultipart()
            message["to"] = from_email
            message["subject"] = subject
            message.attach(MIMEText(body))

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {"raw": raw, "threadId": thread_id}

            return self.service.users().messages().send(userId="me", body=send_message).execute()

        except Exception as e:
            msg = f"Failed to reply to thread: {e!s}"
            raise RuntimeError(msg) from e

    # ADVANCED FEATURES (like Notion/Lark)

    def star_message(self, message_id: str):
        """Star/favorite a message."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": ["STARRED"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to star message: {e!s}"
            raise RuntimeError(msg) from e

    def unstar_message(self, message_id: str):
        """Unstar a message."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"removeLabelIds": ["STARRED"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to unstar message: {e!s}"
            raise RuntimeError(msg) from e

    def archive_message(self, message_id: str):
        """Archive a message (remove from inbox)."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to archive message: {e!s}"
            raise RuntimeError(msg) from e

    def move_to_inbox(self, message_id: str):
        """Move a message to inbox."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": ["INBOX"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to move to inbox: {e!s}"
            raise RuntimeError(msg) from e

    def mark_as_spam(self, message_id: str):
        """Mark a message as spam."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": ["SPAM"]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to mark as spam: {e!s}"
            raise RuntimeError(msg) from e

    def add_label(self, message_id: str, label_id: str):
        """Add a label to a message."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": [label_id]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to add label: {e!s}"
            raise RuntimeError(msg) from e

    def remove_label(self, message_id: str, label_id: str):
        """Remove a label from a message."""
        try:
            return (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"removeLabelIds": [label_id]})
                .execute()
            )
        except Exception as e:
            msg = f"Failed to remove label: {e!s}"
            raise RuntimeError(msg) from e

    def create_label(self, name: str, label_list_visibility: str = "labelShow"):
        """
        Create a custom label.

        Args:
            name: Label name
            label_list_visibility: Visibility in label list (labelShow, labelHide)

        Returns:
            Created label object
        """
        try:
            label = {
                "name": name,
                "labelListVisibility": label_list_visibility,
                "messageListVisibility": "show",
            }
            return self.service.users().labels().create(userId="me", body=label).execute()
        except Exception as e:
            msg = f"Failed to create label: {e!s}"
            raise RuntimeError(msg) from e

    def get_attachments(self, message_id: str):
        """
        Get list of attachments in a message.

        Args:
            message_id: Message ID

        Returns:
            List of attachment metadata
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            attachments = []
            payload = message.get("payload", {})

            def extract_attachments(parts):
                for part in parts:
                    if part.get("filename"):
                        attachments.append(
                            {
                                "filename": part["filename"],
                                "mimeType": part.get("mimeType"),
                                "size": part.get("body", {}).get("size", 0),
                                "attachmentId": part.get("body", {}).get("attachmentId"),
                            }
                        )
                    if "parts" in part:
                        extract_attachments(part["parts"])

            if "parts" in payload:
                extract_attachments(payload["parts"])

            return attachments

        except Exception as e:
            msg = f"Failed to get attachments: {e!s}"
            raise RuntimeError(msg) from e

    def get_profile(self):
        """
        Get user's Gmail profile information.

        Returns:
            Profile object with email address and stats
        """
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return {
                "email": profile.get("emailAddress"),
                "messages_total": profile.get("messagesTotal", 0),
                "threads_total": profile.get("threadsTotal", 0),
                "history_id": profile.get("historyId"),
            }
        except Exception as e:
            msg = f"Failed to get profile: {e!s}"
            raise RuntimeError(msg) from e
