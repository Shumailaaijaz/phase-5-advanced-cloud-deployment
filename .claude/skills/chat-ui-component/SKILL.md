---
name: chat-ui-component
description: Create Next.js components for chatbot interface using Tailwind CSS with accessibility compliance. Use when implementing the chat UI for the AI todo assistant.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Chat UI Component Skill

## Purpose

Create Next.js components for the chatbot interface with Tailwind CSS styling, ARIA accessibility compliance, and optimistic UI updates for a real-time feel.

## Used by

- chat-ui-specialist agent
- frontend-integrator agent

## When to Use

- Building the main chat interface component
- Creating message display components
- Implementing chat input forms
- Adding conversation list/history UI

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `component_name` | string | Yes | Component name (e.g., "TodoChatbot") |
| `props_schema` | object | Yes | Interface for component props |
| `styling` | string | Yes | Styling approach ("tailwind") |
| `endpoint` | string | Yes | Chat API endpoint path |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `component_file` | TSX code | React/Next.js component |
| `types_file` | TS code | TypeScript interfaces |
| `is_accessible` | boolean | ARIA compliance confirmation |

## Core Implementation

### Main Chat Component

```typescript
// File: app/components/TodoChatbot.tsx
// [Skill]: Chat UI Component

'use client'

import { useState, useRef, useEffect } from 'react'
import { useUser } from '@/hooks/useUser'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  pending?: boolean
}

interface TodoChatbotProps {
  conversationId?: string
  onConversationCreate?: (id: string) => void
}

export default function TodoChatbot({
  conversationId,
  onConversationCreate
}: TodoChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { userId } = useUser()

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load conversation history
  useEffect(() => {
    if (conversationId) {
      loadHistory()
    }
  }, [conversationId])

  const loadHistory = async () => {
    try {
      const res = await fetch(`/api/${userId}/conversations/${conversationId}`)
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: new Date(m.created_at)
        })))
      }
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setError(null)

    // Optimistic UI update
    const tempId = `temp-${Date.now()}`
    const newUserMsg: Message = {
      id: tempId,
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
      pending: true
    }
    setMessages(prev => [...prev, newUserMsg])
    setIsLoading(true)

    try {
      const response = await fetch(`/api/${userId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: userMessage
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()

      // Update with real IDs and add assistant response
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempId),
        { ...newUserMsg, id: data.user_message_id, pending: false },
        {
          id: data.assistant_message_id,
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        }
      ])

      // Notify parent of new conversation
      if (!conversationId && data.conversation_id) {
        onConversationCreate?.(data.conversation_id)
      }

    } catch (err) {
      setError('Failed to send message. Please try again.')
      // Remove pending message on error
      setMessages(prev => prev.filter(m => m.id !== tempId))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div
      className="flex flex-col h-full bg-white rounded-lg shadow-lg"
      role="region"
      aria-label="Todo Chatbot"
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">
          Todo Assistant
        </h2>
        <p className="text-sm text-gray-500">
          Manage your tasks with natural language
        </p>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-8">
            <p>Start a conversation to manage your todos!</p>
            <p className="text-sm mt-2">Try: "Add a task to buy groceries"</p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-gray-400">
            <LoadingDots />
            <span className="text-sm">Assistant is typing...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div
          className="mx-4 mb-2 p-2 bg-red-50 text-red-600 text-sm rounded"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-gray-200"
      >
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg
                     focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:bg-gray-100 disabled:cursor-not-allowed"
            aria-label="Chat input"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg
                     hover:bg-blue-700 focus:outline-none focus:ring-2
                     focus:ring-blue-500 disabled:bg-gray-400
                     disabled:cursor-not-allowed transition-colors"
            aria-label="Send message"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}
```

### Message Component

```typescript
// File: app/components/ChatMessage.tsx
// [Skill]: Chat UI Component

import { Message } from '@/types/chat'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      role="article"
      aria-label={`${message.role} message`}
    >
      <div
        className={`max-w-[80%] px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
        } ${message.pending ? 'opacity-70' : ''}`}
      >
        <p className="whitespace-pre-wrap break-words">
          {message.content}
        </p>
        <span
          className={`text-xs ${isUser ? 'text-blue-200' : 'text-gray-400'}
                    block mt-1`}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>
    </div>
  )
}
```

### Loading Indicator

```typescript
// File: app/components/LoadingDots.tsx
// [Skill]: Chat UI Component

export function LoadingDots() {
  return (
    <div className="flex space-x-1" aria-hidden="true">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
           style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
           style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
           style={{ animationDelay: '300ms' }} />
    </div>
  )
}
```

### Types

```typescript
// File: types/chat.ts
// [Skill]: Chat UI Component

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  pending?: boolean
}

export interface Conversation {
  id: string
  title?: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ChatResponse {
  conversation_id: string
  user_message_id: string
  assistant_message_id: string
  response: string
}

export interface TodoChatbotProps {
  conversationId?: string
  onConversationCreate?: (id: string) => void
}
```

### Conversation List Component

```typescript
// File: app/components/ConversationList.tsx
// [Skill]: Chat UI Component

'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@/hooks/useUser'
import { Conversation } from '@/types/chat'

interface ConversationListProps {
  activeId?: string
  onSelect: (id: string) => void
  onNew: () => void
}

export function ConversationList({
  activeId,
  onSelect,
  onNew
}: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const { userId } = useUser()

  useEffect(() => {
    loadConversations()
  }, [userId])

  const loadConversations = async () => {
    try {
      const res = await fetch(`/api/${userId}/conversations`)
      if (res.ok) {
        const data = await res.json()
        setConversations(data.conversations)
      }
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <div className="p-4 border-b">
        <button
          onClick={onNew}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg
                   hover:bg-blue-700 transition-colors"
          aria-label="Start new conversation"
        >
          New Chat
        </button>
      </div>

      <nav
        className="flex-1 overflow-y-auto"
        aria-label="Conversation history"
      >
        <ul className="p-2 space-y-1">
          {conversations.map((conv) => (
            <li key={conv.id}>
              <button
                onClick={() => onSelect(conv.id)}
                className={`w-full text-left px-3 py-2 rounded-lg
                         transition-colors ${
                  activeId === conv.id
                    ? 'bg-blue-100 text-blue-800'
                    : 'hover:bg-gray-200'
                }`}
                aria-current={activeId === conv.id ? 'true' : undefined}
              >
                <span className="block truncate font-medium">
                  {conv.title || 'New Conversation'}
                </span>
                <span className="block text-xs text-gray-500">
                  {new Date(conv.updated_at).toLocaleDateString()}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
```

## Quality Standards

### State Management
- Local state for UI (messages, input, loading)
- Database for persistence (via API)
- Optimistic updates for instant feedback

### Accessibility (ARIA)
- `role="region"` for chat container
- `role="log"` with `aria-live="polite"` for messages
- `role="alert"` for error messages
- `aria-label` on all interactive elements
- Keyboard navigable

### Real-time Feel
- Optimistic UI updates (show user message immediately)
- Loading indicator while waiting for response
- Smooth auto-scroll to new messages

### Error Handling
- User-friendly error messages
- Graceful fallback on network errors
- Pending state visual indicator

## Verification Checklist

- [ ] Component uses 'use client' directive
- [ ] ARIA roles and labels on all regions
- [ ] Optimistic UI updates implemented
- [ ] Loading state with visual indicator
- [ ] Error display with `role="alert"`
- [ ] Auto-scroll to new messages
- [ ] Keyboard accessible (Tab, Enter)
- [ ] Tailwind classes for responsive design
- [ ] TypeScript interfaces defined

## Output Format

1. **Main component** in `app/components/TodoChatbot.tsx`
2. **Message component** in `app/components/ChatMessage.tsx`
3. **Types** in `types/chat.ts`
4. **Supporting components** as needed
