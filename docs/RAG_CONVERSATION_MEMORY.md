# RAG-Enhanced Conversation Memory System

## Overview

This document explains the RAG (Retrieval-Augmented Generation) implementation for intelligent conversation context management in the Chronus AI chat system.

## Problem Statement

**Before:** The AI would forget conversation context after a few turns because:

- Agent instances stored conversation history in memory only
- When continuing an existing conversation, the agent didn't load previous messages from the database
- Loading all 50 messages was inefficient and wasted tokens on irrelevant context

## Solution: RAG-Based Context Retrieval

### Architecture

```
User Message
    ↓
┌─────────────────────────────────────────────────┐
│  1. Recent Messages (Last 6)                    │
│     - Immediate chronological context           │
│     - Last 3 user-assistant exchanges           │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  2. Semantic Search - Current Conversation      │
│     - VectorDB finds top 5 relevant messages    │
│     - Based on semantic similarity to query     │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  3. Semantic Search - Other Conversations       │
│     - VectorDB finds top 3 related messages     │
│     - Cross-conversation memory                 │
│     - Filtered to exclude current conversation  │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  4. Context Injection                           │
│     - RAG context (semantically relevant)       │
│     - Recent history (chronological)            │
│     - Combined into AI prompt                   │
└─────────────────────────────────────────────────┘
    ↓
AI Response with Full Context
```

### Key Components

#### 1. **VectorDB Integration** (`/app/services/vector_db.py`)

- **Qdrant** for vector storage
- **Google Gemini Embeddings** (768 dimensions)
- **Collections:**
  - `chat_messages`: All user/assistant messages
  - `knowledge_base`: Additional knowledge documents

#### 2. **Chat API** (`/app/api/v1/chat.py`)

```python
# RAG-based context retrieval
if request.conversation_id:
    # 1. Recent messages (6 messages = 3 exchanges)
    recent_messages = await chat_service.get_conversation_history(
        conversation_id=conversation_id,
        limit=6
    )

    # 2. Relevant from current conversation
    relevant_current = await chat_service.get_relevant_context(
        query=request.message,
        current_conversation_id=conversation_id,
        max_messages=5
    )

    # 3. Relevant from other conversations
    relevant_other = await vector_db_service.search_chat_history(
        query=request.message,
        user_id=str(user_id),
        limit=3
    )
```

#### 3. **Agent Service** (`/app/services/ai/agent_service.py`)

```python
# Inject RAG context into prompt
full_history = rag_context_str + history_context

# Context structure:
# 1. RELEVANT CONTEXT FROM THIS CONVERSATION
# 2. RELATED CONTEXT FROM PAST CONVERSATIONS
# 3. RECENT CONVERSATION HISTORY
```

### Benefits

#### 🎯 **Token Efficiency**

- **Before:** 50 messages × ~100 tokens = ~5,000 tokens
- **After:** 6 recent + 5 relevant + 3 related = ~14 messages × ~100 tokens = ~1,400 tokens
- **Savings:** ~72% reduction in context tokens

#### 🧠 **Better Context**

- Semantic search finds **actually relevant** messages
- Not limited to chronological order
- Can reference related past conversations
- AI gets exactly what it needs to answer

#### 🔄 **Cross-Conversation Memory**

- AI can remember related discussions from other conversations
- Example: "Remember when we talked about that project?" works even if it was in a different conversation

#### 📈 **Scalability**

- Works with conversations of any length
- Performance doesn't degrade as conversations grow
- VectorDB handles millions of messages efficiently

### How It Works

#### Message Storage

1. User sends message → Saved to PostgreSQL
2. Message content → Embedded using Gemini
3. Embedding → Stored in Qdrant VectorDB
4. Metadata attached: `user_id`, `conversation_id`, `role`

#### Context Retrieval

1. User sends new message
2. Message → Embedded using Gemini
3. VectorDB searches for similar embeddings (cosine similarity)
4. Returns top-k most relevant messages with scores
5. Context injected into AI prompt

#### Prompt Structure

```
RELEVANT CONTEXT FROM THIS CONVERSATION:
1. User: [semantically relevant message from earlier in this conversation]
2. Assistant: [relevant response]

RELATED CONTEXT FROM PAST CONVERSATIONS:
1. User (relevance: 0.85): [related message from another conversation]
2. Assistant (relevance: 0.82): [related response]

RECENT CONVERSATION HISTORY:
1. User: [message from 3 turns ago]
2. Assistant: [response from 3 turns ago]
3. User: [message from 2 turns ago]
4. Assistant: [response from 2 turns ago]
5. User: [message from 1 turn ago]
6. Assistant: [response from 1 turn ago]

Question: [current user message]
```

### Configuration

#### Tunable Parameters

```python
# In chat.py
recent_messages_limit = 6        # Last N messages for immediate context
relevant_current_limit = 5       # Top N relevant from current conversation
relevant_other_limit = 3         # Top N relevant from other conversations

# In agent_service.py
conversation_history_window = 10 # Last N messages to include in prompt
```

#### Recommendations

- **Short conversations:** Increase `recent_messages_limit` to 10
- **Long conversations:** Keep at 6, rely more on semantic search
- **Memory-intensive tasks:** Increase `relevant_current_limit` to 8-10
- **Cross-conversation needs:** Increase `relevant_other_limit` to 5

### Testing

#### Test Scenarios

1. **Multi-turn conversation:** AI should remember context from 5+ turns ago
2. **Topic switch:** AI should retrieve relevant old messages when topic returns
3. **Cross-conversation:** Ask about something discussed in a different conversation
4. **Token efficiency:** Monitor token usage in Gemini API dashboard

#### Example Test

```
Conversation 1:
User: "I'm planning a trip to Japan in March"
AI: "That's exciting! March is cherry blossom season..."

[New Conversation 2, days later]
User: "What was that trip I mentioned?"
AI: [Should retrieve context from Conversation 1]
```

### Performance Considerations

#### VectorDB Performance

- **Embedding generation:** ~100-200ms per message
- **Vector search:** ~10-50ms for top-k retrieval
- **Total overhead:** ~150-250ms per message

#### Trade-offs

- **Pros:** Better context, token savings, scalability
- **Cons:** Slight latency increase, requires VectorDB infrastructure

### Future Enhancements

1. **Adaptive Context Window**

   - Dynamically adjust based on conversation complexity
   - Use fewer messages for simple queries, more for complex ones

2. **Conversation Summarization**

   - Summarize very long conversations
   - Store summaries in VectorDB for even better retrieval

3. **User Preferences**

   - Let users control how much context to use
   - "Remember everything" vs "Focus on recent" modes

4. **Hybrid Search**

   - Combine semantic search with keyword search
   - Better handling of specific names, dates, etc.

5. **Context Ranking**
   - Use LLM to re-rank retrieved context
   - Filter out truly irrelevant results

## Conclusion

The RAG-based approach provides:

- ✅ **72% token savings** compared to loading all messages
- ✅ **Better context** through semantic search
- ✅ **Cross-conversation memory** for related topics
- ✅ **Scalability** for conversations of any length

The AI now truly "remembers" conversations intelligently, not just chronologically.
