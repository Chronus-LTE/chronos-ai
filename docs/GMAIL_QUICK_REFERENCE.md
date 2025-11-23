# Gmail API Quick Reference

## 🚀 Quick Start

### 1. Authentication

Users must login with Google OAuth to grant Gmail access.

### 2. API Base URL

```
http://localhost:8000/api/v1/gmail
```

### 3. Authentication Header

```
Authorization: Bearer <your-jwt-token>
```

---

## 📧 API Endpoints

### List Messages

```http
GET /messages?max_results=20&query=is:unread
```

### Search Messages

```http
GET /messages/search?query=from:example@gmail.com
```

### Get Message

```http
GET /messages/{message_id}
```

### Send Email

```http
POST /messages/send
{
  "to": "recipient@example.com",
  "subject": "Subject",
  "body": "Body content"
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

### Get Labels

```http
GET /labels
```

---

## 🔍 Gmail Search Queries

| Query                    | Description              |
| ------------------------ | ------------------------ |
| `is:unread`              | Unread messages          |
| `is:read`                | Read messages            |
| `from:email@example.com` | From specific sender     |
| `to:email@example.com`   | To specific recipient    |
| `subject:keyword`        | Subject contains keyword |
| `has:attachment`         | Has attachments          |
| `label:important`        | Has "important" label    |
| `after:2024/01/01`       | After specific date      |
| `before:2024/12/31`      | Before specific date     |
| `newer_than:7d`          | Newer than 7 days        |
| `older_than:30d`         | Older than 30 days       |

**Combine queries:**

```
is:unread from:boss@company.com
subject:urgent has:attachment
```

---

## 🤖 AI Agent Commands

### English

```
"Do I have any unread emails?"
"Show me my recent emails"
"List emails from john@example.com"
"Search for emails about meeting"
"Send an email to jane@example.com with subject 'Test' and body 'Hello'"
"Mark email [ID] as read"
"How many unread emails do I have?"
```

### Vietnamese

```
"Tôi có email chưa đọc không?"
"Cho tôi xem email gần đây"
"Tìm email từ john@example.com"
"Tìm email về cuộc họp"
"Gửi email cho jane@example.com với tiêu đề 'Test' và nội dung 'Xin chào'"
"Đánh dấu email [ID] là đã đọc"
"Tôi có bao nhiêu email chưa đọc?"
```

---

## 📝 Code Examples

### Python (using httpx)

```python
import httpx

TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

async with httpx.AsyncClient() as client:
    # List messages
    response = await client.get(
        "http://localhost:8000/api/v1/gmail/messages?max_results=10",
        headers=headers
    )

    # Send email
    response = await client.post(
        "http://localhost:8000/api/v1/gmail/messages/send",
        headers=headers,
        json={
            "to": "recipient@example.com",
            "subject": "Test",
            "body": "Hello!"
        }
    )
```

### JavaScript (using fetch)

```javascript
const TOKEN = "your-jwt-token";
const headers = {
  Authorization: `Bearer ${TOKEN}`,
  "Content-Type": "application/json",
};

// List messages
const response = await fetch(
  "http://localhost:8000/api/v1/gmail/messages?max_results=10",
  { headers }
);

// Send email
const response = await fetch(
  "http://localhost:8000/api/v1/gmail/messages/send",
  {
    method: "POST",
    headers,
    body: JSON.stringify({
      to: "recipient@example.com",
      subject: "Test",
      body: "Hello!",
    }),
  }
);
```

### cURL

```bash
# List messages
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/gmail/messages?max_results=10"

# Send email
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"Test","body":"Hello"}' \
  "http://localhost:8000/api/v1/gmail/messages/send"
```

---

## 📊 Response Format

### Email Object

```json
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
```

### List Response

```json
{
  "emails": [
    /* array of email objects */
  ],
  "count": 10
}
```

### Send Response

```json
{
  "message": "Email sent successfully",
  "id": "message_id",
  "threadId": "thread_id"
}
```

---

## ⚠️ Error Codes

| Code | Description                                              |
| ---- | -------------------------------------------------------- |
| 400  | Bad Request - Invalid parameters or missing Gmail access |
| 401  | Unauthorized - Invalid or missing token                  |
| 404  | Not Found - Message not found                            |
| 500  | Internal Server Error - Gmail API error                  |

---

## 🔧 Gmail Service (Python)

```python
from app.services.google.gmail_service import GoogleGmailService

# Initialize
gmail = GoogleGmailService(
    token=user.google_access_token,
    refresh_token=user.google_refresh_token
)

# List messages
messages = gmail.list_messages(max_results=10, query="is:unread")

# Get message
message = gmail.get_message(message_id)

# Send email
gmail.send_message(
    to="recipient@example.com",
    subject="Subject",
    body="Body"
)

# Search
results = gmail.search_messages(query="from:example@gmail.com")

# Mark as read/unread
gmail.mark_as_read(message_id)
gmail.mark_as_unread(message_id)

# Delete
gmail.delete_message(message_id)

# Get labels
labels = gmail.get_labels()

# Get unread count
count = gmail.get_unread_count()
```

---

## 📚 More Information

- Full documentation: [GMAIL_INTEGRATION.md](GMAIL_INTEGRATION.md)
- Implementation summary: [GMAIL_IMPLEMENTATION_SUMMARY.md](GMAIL_IMPLEMENTATION_SUMMARY.md)
- Test script: `scripts/test_gmail.py`
