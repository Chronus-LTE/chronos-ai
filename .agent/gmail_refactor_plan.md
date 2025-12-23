# Gmail Feature - Complete Refactor Plan

## 🎯 Objectives

1. ✅ Hoàn thiện đầy đủ chức năng Gmail (như Notion/Lark)
2. ✅ Clean code architecture
3. ✅ Remove duplicates và deprecated endpoints
4. ✅ Optimize performance
5. ✅ Add missing features

---

## 📋 Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                                │
│  ┌──────────────┐              ┌──────────────┐             │
│  │ /gmail       │              │ /gmail/sync  │             │
│  │ (Real-time)  │              │ (Cached)     │             │
│  └──────────────┘              └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────────┐       ┌──────────────────┐            │
│  │ GmailService     │       │ EmailSyncService │            │
│  │ (Gmail API)      │       │ (Sync Logic)     │            │
│  └──────────────────┘       └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Email    │  │ Thread   │  │ Label    │  │ SyncState│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Refactor Tasks

### Phase 1: Consolidate API Endpoints ✅

**Goal:** Merge duplicate endpoints, deprecate old ones

#### 1.1 Create Unified Gmail Router

- [ ] Create `/api/v1/gmail_unified.py`
- [ ] Combine best of both `/gmail` and `/gmail/sync`
- [ ] Clear separation: Actions vs Queries

#### 1.2 Endpoint Mapping

**KEEP (Actions - Real-time):**

```python
POST   /gmail/send              # Send email
POST   /gmail/drafts            # Create draft
POST   /gmail/drafts/{id}/send  # Send draft
POST   /gmail/threads/{id}/reply # Reply to thread
```

**KEEP (Queries - Cached):**

```python
GET    /gmail/emails            # List emails (from DB)
GET    /gmail/emails/{id}       # Get email detail
GET    /gmail/threads/{id}      # Get thread
GET    /gmail/search            # Search emails
GET    /gmail/labels            # Get labels
GET    /gmail/unread-count      # Unread count
```

**KEEP (Updates - Sync both):**

```python
POST   /gmail/emails/{id}/mark-read
POST   /gmail/emails/{id}/star
POST   /gmail/emails/{id}/archive
DELETE /gmail/emails/{id}
```

**KEEP (Sync Management):**

```python
POST   /gmail/sync/start        # Trigger sync
GET    /gmail/sync/status       # Sync status
```

**DEPRECATE:**

```python
❌ /gmail/messages              → Use /gmail/emails
❌ /gmail/messages/{id}         → Use /gmail/emails/{id}
❌ /gmail/sync/emails           → Use /gmail/emails
```

### Phase 2: Enhance Models ✅

#### 2.1 Add Missing Fields

- [ ] Add `EmailThread` relationship to `Email`
- [ ] Add attachment parsing to sync
- [ ] Add email categories/importance

#### 2.2 Add Indexes

- [ ] Full-text search index on subject/body
- [ ] Composite indexes for common queries

### Phase 3: Complete Service Layer ✅

#### 3.1 GmailService Enhancements

- [ ] Add batch operations
- [ ] Add attachment download
- [ ] Add email forwarding
- [ ] Add label management (create/update/delete)

#### 3.2 EmailSyncService Enhancements

- [ ] Add thread sync logic
- [ ] Add attachment sync
- [ ] Add smart sync (priority inbox first)
- [ ] Add conflict resolution

### Phase 4: Background Tasks ✅

#### 4.1 Celery Tasks

- [x] Initial sync
- [x] Incremental sync
- [x] Periodic sync all users
- [ ] Smart sync (based on user activity)
- [ ] Attachment download queue

#### 4.2 Celery Beat Schedule

```python
CELERY_BEAT_SCHEDULE = {
    'sync-all-users': {
        'task': 'sync_all_users',
        'schedule': crontab(minute='*/10'),  # Every 10 min
    },
    'cleanup-old-emails': {
        'task': 'cleanup_old_emails',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

### Phase 5: Advanced Features 🆕

#### 5.1 Smart Features

- [ ] Email categorization (Primary/Social/Promotions)
- [ ] Priority inbox
- [ ] Smart replies suggestions
- [ ] Email templates
- [ ] Scheduled sending

#### 5.2 Analytics

- [ ] Email stats (sent/received per day)
- [ ] Response time analytics
- [ ] Top senders/recipients
- [ ] Attachment analytics

#### 5.3 Webhooks

- [ ] Gmail push notifications setup
- [ ] Real-time sync via webhooks
- [ ] Webhook endpoint `/gmail/webhook`

---

## 📁 New File Structure

```
app/
├── api/v1/
│   ├── gmail.py              # Unified Gmail API (refactored)
│   └── gmail_webhooks.py     # Webhook handlers (NEW)
├── services/
│   ├── google/
│   │   ├── gmail_service.py          # Gmail API wrapper (enhanced)
│   │   └── gmail_batch_service.py    # Batch operations (NEW)
│   ├── email_sync_service.py         # Sync logic (enhanced)
│   └── email_analytics_service.py    # Analytics (NEW)
├── models/
│   └── email.py              # Email models (enhanced)
├── tasks/
│   ├── gmail_sync_tasks.py   # Sync tasks (enhanced)
│   └── gmail_analytics_tasks.py # Analytics tasks (NEW)
└── schemas/
    └── gmail.py              # Pydantic schemas (NEW)
```

---

## 🚀 Implementation Order

1. **Create schemas** (Pydantic models for validation)
2. **Refactor gmail.py** (unified endpoints)
3. **Enhance services** (add missing features)
4. **Add webhooks** (real-time sync)
5. **Add analytics** (insights)
6. **Update frontend** (use new endpoints)
7. **Deprecate old endpoints** (with warnings)
8. **Remove old code** (after migration)

---

## ✅ Success Criteria

- [ ] All Gmail features working (send, receive, search, etc.)
- [ ] Fast queries (< 100ms for list, < 50ms for count)
- [ ] Real-time sync (< 5 sec delay)
- [ ] Clean code (no duplicates, clear separation)
- [ ] Well documented (docstrings, API docs)
- [ ] Tested (unit + integration tests)

---

## 📊 Performance Targets

| Operation                  | Target  | Current |
| -------------------------- | ------- | ------- |
| List emails                | < 100ms | ?       |
| Get email detail           | < 50ms  | ?       |
| Unread count               | < 20ms  | ?       |
| Search                     | < 200ms | ?       |
| Send email                 | < 2s    | ?       |
| Initial sync (1000 emails) | < 5 min | ?       |
| Incremental sync           | < 30s   | ?       |

---

## 🔐 Security Considerations

- [ ] Rate limiting on API endpoints
- [ ] Token refresh handling
- [ ] Secure attachment storage
- [ ] Email content encryption (optional)
- [ ] Audit logging for sensitive operations
