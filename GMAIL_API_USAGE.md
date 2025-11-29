# Gmail API Usage Guide 📧

## Overview

The Gmail API provides fast local database queries with filtering and pagination support.

## Base URL

```
http://localhost:8000/api/v1/gmail
```

---

## 📬 List Emails with Filters

### Endpoint

```
GET /api/v1/gmail/emails
```

### Query Parameters

| Parameter      | Type    | Default | Description                       |
| -------------- | ------- | ------- | --------------------------------- |
| `limit`        | int     | 20      | Number of emails per page (1-100) |
| `offset`       | int     | 0       | Offset for pagination             |
| `label`        | string  | null    | Filter by Gmail label             |
| `unread_only`  | boolean | false   | Only show unread emails           |
| `starred_only` | boolean | false   | Only show starred emails          |

### Common Gmail Labels

- `INBOX` - Inbox emails
- `SENT` - Sent emails
- `TRASH` - Deleted emails
- `DRAFT` - Draft emails
- `STARRED` - Starred emails
- `IMPORTANT` - Important emails
- `SPAM` - Spam emails
- `CATEGORY_PERSONAL` - Personal category
- `CATEGORY_SOCIAL` - Social category
- `CATEGORY_PROMOTIONS` - Promotions category
- `CATEGORY_UPDATES` - Updates category

---

## 📋 Usage Examples

### 1. Get Inbox (First Page)

```bash
GET /api/v1/gmail/emails?label=INBOX&limit=20&offset=0
```

**Response:**

```json
{
  "emails": [
    {
      "id": 123,
      "gmail_id": "18c1a2b3c4d5e6f7",
      "thread_id": "18c1a2b3c4d5e6f7",
      "subject": "Meeting Tomorrow",
      "from": "boss@company.com",
      "to": "you@company.com",
      "date": "2024-11-29T10:30:00Z",
      "snippet": "Don't forget our meeting...",
      "labels": ["INBOX", "IMPORTANT"],
      "is_unread": true,
      "is_starred": false,
      "has_attachments": false
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### 2. Get Sent Emails

```bash
GET /api/v1/gmail/emails?label=SENT&limit=20&offset=0
```

### 3. Get Trash

```bash
GET /api/v1/gmail/emails?label=TRASH&limit=20&offset=0
```

### 4. Get Drafts

```bash
GET /api/v1/gmail/emails?label=DRAFT&limit=20&offset=0
```

### 5. Get Starred Emails

```bash
GET /api/v1/gmail/emails?starred_only=true&limit=20&offset=0
```

### 6. Get Unread Inbox

```bash
GET /api/v1/gmail/emails?label=INBOX&unread_only=true&limit=20&offset=0
```

### 7. Pagination (Page 2)

```bash
GET /api/v1/gmail/emails?label=INBOX&limit=20&offset=20
```

### 8. Pagination (Page 3)

```bash
GET /api/v1/gmail/emails?label=INBOX&limit=20&offset=40
```

---

## 🔢 Pagination Logic

```typescript
// Frontend pagination example
const PAGE_SIZE = 20;

function getEmails(page: number, label: string) {
  const offset = page * PAGE_SIZE;
  return fetch(
    `/api/v1/gmail/emails?label=${label}&limit=${PAGE_SIZE}&offset=${offset}`
  );
}

// Usage
getEmails(0, "INBOX"); // Page 1
getEmails(1, "INBOX"); // Page 2
getEmails(2, "INBOX"); // Page 3
```

---

## 📊 Get Unread Count

### Endpoint

```
GET /api/v1/gmail/unread-count
```

**Response:**

```json
{
  "unread_count": 42
}
```

---

## 🔄 Sync Management

### Start Sync

```
POST /api/v1/gmail/sync
```

**Request Body:**

```json
{
  "force_full": false,
  "max_messages": 1000
}
```

**Response:**

```json
{
  "message": "Initial sync started",
  "sync_type": "initial",
  "status": "syncing"
}
```

### Check Sync Status

```
GET /api/v1/gmail/sync/status
```

**Response:**

```json
{
  "status": "syncing",
  "sync_type": "initial",
  "total_messages": 500,
  "synced_messages": 250,
  "failed_messages": 0,
  "progress_percentage": 50.0,
  "last_sync_date": null,
  "last_error": null
}
```

---

## 🎯 Frontend Implementation Example

### React/Angular Component

```typescript
// Mail Sidebar Component
const folders = [
  { name: "Inbox", label: "INBOX", icon: "inbox" },
  { name: "Sent", label: "SENT", icon: "send" },
  { name: "Drafts", label: "DRAFT", icon: "draft" },
  { name: "Starred", label: null, starred: true, icon: "star" },
  { name: "Trash", label: "TRASH", icon: "delete" },
];

function loadFolder(folder) {
  const params = new URLSearchParams({
    limit: "20",
    offset: "0",
  });

  if (folder.label) {
    params.append("label", folder.label);
  }

  if (folder.starred) {
    params.append("starred_only", "true");
  }

  fetch(`/api/v1/gmail/emails?${params}`)
    .then((res) => res.json())
    .then((data) => {
      setEmails(data.emails);
      setTotalPages(Math.ceil(data.total / data.limit));
      setHasMore(data.has_more);
    });
}
```

### Pagination Component

```typescript
function EmailPagination({ currentPage, totalPages, onPageChange }) {
  return (
    <div className="pagination">
      <button
        disabled={currentPage === 0}
        onClick={() => onPageChange(currentPage - 1)}
      >
        Previous
      </button>

      <span>
        Page {currentPage + 1} of {totalPages}
      </span>

      <button
        disabled={currentPage >= totalPages - 1}
        onClick={() => onPageChange(currentPage + 1)}
      >
        Next
      </button>
    </div>
  );
}
```

---

## 🚀 Performance Tips

1. **Use local DB queries** - Much faster than Gmail API
2. **Implement infinite scroll** - Better UX than traditional pagination
3. **Cache results** - Reduce API calls
4. **Poll sync status** - Show real-time progress during sync
5. **Debounce search** - Avoid excessive API calls

---

## 🔍 Search Emails

### Endpoint

```
GET /api/v1/gmail/search?q=meeting&limit=20
```

Searches in: subject, from, to, body

---

## ⚡ Actions

### Mark as Read

```
POST /api/v1/gmail/emails/{email_id}/mark-read
```

### Mark as Unread

```
POST /api/v1/gmail/emails/{email_id}/mark-unread
```

### Star Email

```
POST /api/v1/gmail/emails/{email_id}/star
```

### Unstar Email

```
POST /api/v1/gmail/emails/{email_id}/unstar
```

### Delete Email

```
DELETE /api/v1/gmail/emails/{email_id}
```

---

## 📱 Complete Frontend Flow

```typescript
// 1. Initialize - Check sync status
const syncStatus = await fetch("/api/v1/gmail/sync/status").then((r) =>
  r.json()
);

if (syncStatus.status === "pending") {
  // 2. Start initial sync
  await fetch("/api/v1/gmail/sync", { method: "POST" });

  // 3. Poll for progress
  const interval = setInterval(async () => {
    const status = await fetch("/api/v1/gmail/sync/status").then((r) =>
      r.json()
    );
    updateProgressBar(status.progress_percentage);

    if (status.status === "completed") {
      clearInterval(interval);
      loadEmails();
    }
  }, 2000);
}

// 4. Load emails by folder
function loadEmails(label = "INBOX", page = 0) {
  const offset = page * 20;
  fetch(`/api/v1/gmail/emails?label=${label}&limit=20&offset=${offset}`)
    .then((r) => r.json())
    .then((data) => {
      displayEmails(data.emails);
      updatePagination(data.total, data.limit, data.offset);
    });
}

// 5. Get unread count for badge
fetch("/api/v1/gmail/unread-count")
  .then((r) => r.json())
  .then((data) => updateBadge(data.unread_count));
```
