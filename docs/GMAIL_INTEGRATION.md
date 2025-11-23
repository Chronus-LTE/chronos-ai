# Gmail Integration

This document describes the Gmail integration in Chronus AI, which allows both the AI agent and client applications to interact with Gmail.

## Features

### For AI Agent

The AI agent can:

- 📧 Read and list emails
- 🔍 Search emails using Gmail search syntax
- ✉️ Send emails
- ✅ Mark emails as read/unread
- 📊 Get unread count

### For Client Applications

Client apps can directly access Gmail through REST API endpoints:

- List messages
- Search messages
- Read specific messages
- Send emails
- Manage email labels (read/unread)
- Get unread count
- Get Gmail labels

## Setup

### 1. OAuth Scopes

The following Gmail scopes are automatically requested during Google OAuth login:

```python
"https://www.googleapis.com/auth/gmail.readonly"  # Read emails
"https://www.googleapis.com/auth/gmail.send"      # Send emails
"https://www.googleapis.com/auth/gmail.modify"    # Modify emails (labels, etc)
```

### 2. User Authentication

Users must authenticate with Google OAuth to grant Gmail access. The access token is stored in the database and used for all Gmail operations.

## API Endpoints

Base URL: `/api/v1/gmail`

### List Messages

```http
GET /messages?max_results=20&query=is:unread
```

**Query Parameters:**

- `max_results` (optional): Maximum number of messages to return (default: 20)
- `query` (optional): Gmail search query

**Response:**

```json
{
  "emails": [
    {
      "id": "message_id",
      "threadId": "thread_id",
      "subject": "Email Subject",
      "from": "sender@example.com",
      "to": "recipient@example.com",
      "date": "Mon, 23 Nov 2025 10:30:00 +0700",
      "snippet": "Email preview...",
      "body": "Full email body...",
      "labels": ["INBOX", "UNREAD"],
      "isUnread": true
    }
  ],
  "count": 1
}
```

### Search Messages

```http
GET /messages/search?query=from:example@gmail.com&max_results=10
```

**Gmail Search Query Examples:**

- `is:unread` - Unread messages
- `from:example@gmail.com` - From specific sender
- `subject:meeting` - Subject contains "meeting"
- `has:attachment` - Has attachments
- `after:2024/01/01` - After specific date
- `label:important` - Has "important" label

### Get Message

```http
GET /messages/{message_id}
```

**Response:** Single email object (same structure as list)

### Send Email

```http
POST /messages/send
Content-Type: application/json

{
  "to": "recipient@example.com",
  "subject": "Email Subject",
  "body": "Email body content"
}
```

**Response:**

```json
{
  "message": "Email sent successfully",
  "id": "message_id",
  "threadId": "thread_id"
}
```

### Mark as Read

```http
POST /messages/{message_id}/mark-read
```

### Mark as Unread

```http
POST /messages/{message_id}/mark-unread
```

### Delete Message

```http
DELETE /messages/{message_id}
```

### Get Unread Count

```http
GET /unread-count
```

**Response:**

```json
{
  "unread_count": 5
}
```

### Get Labels

```http
GET /labels
```

**Response:**

```json
{
  "labels": [
    {
      "id": "INBOX",
      "name": "INBOX",
      "type": "system"
    },
    {
      "id": "Label_123",
      "name": "Work",
      "type": "user"
    }
  ]
}
```

## AI Agent Usage

The AI agent automatically has access to Gmail tools. Users can interact with their email using natural language:

### Examples

**English:**

```
User: "Do I have any unread emails?"
Agent: "You have 5 unread emails. Would you like me to list them?"

User: "Show me emails from john@example.com"
Agent: [Lists emails from that sender]

User: "Send an email to jane@example.com with subject 'Meeting Tomorrow' and body 'Let's meet at 2pm'"
Agent: "✅ Email sent successfully to jane@example.com"
```

**Vietnamese:**

```
User: "Tôi có email chưa đọc không?"
Agent: "Bạn có 5 email chưa đọc. Bạn muốn xem danh sách không?"

User: "Tìm email từ john@example.com"
Agent: [Liệt kê các email từ người gửi đó]

User: "Gửi email cho jane@example.com với tiêu đề 'Họp ngày mai' và nội dung 'Gặp nhau lúc 2 giờ chiều nhé'"
Agent: "✅ Đã gửi email thành công đến jane@example.com"
```

## Gmail Service

The `GoogleGmailService` class provides the core Gmail functionality:

```python
from app.services.google.gmail_service import GoogleGmailService

# Initialize with user's access token
gmail_service = GoogleGmailService(
    token=user.google_access_token,
    refresh_token=user.google_refresh_token
)

# List messages
messages = gmail_service.list_messages(max_results=10, query="is:unread")

# Get specific message
message = gmail_service.get_message(message_id)

# Send email
gmail_service.send_message(
    to="recipient@example.com",
    subject="Subject",
    body="Body content"
)

# Search emails
results = gmail_service.search_messages(query="from:example@gmail.com")

# Mark as read/unread
gmail_service.mark_as_read(message_id)
gmail_service.mark_as_unread(message_id)

# Delete message (move to trash)
gmail_service.delete_message(message_id)

# Get labels
labels = gmail_service.get_labels()

# Get unread count
count = gmail_service.get_unread_count()
```

## Security Considerations

1. **OAuth Tokens**: Access tokens are stored securely in the database and used only for authenticated requests
2. **User Isolation**: Each user can only access their own emails
3. **Scope Limitation**: Only necessary Gmail scopes are requested
4. **Token Refresh**: Refresh tokens are used to obtain new access tokens when needed

## Error Handling

All Gmail operations include proper error handling:

- **400 Bad Request**: Invalid parameters or missing Gmail access
- **404 Not Found**: Message not found
- **500 Internal Server Error**: Gmail API errors

## Future Enhancements

Potential improvements:

- [ ] Support for email attachments
- [ ] HTML email support
- [ ] Email drafts
- [ ] Email threading
- [ ] Advanced label management
- [ ] Email filters
- [ ] Batch operations
- [ ] Email templates
