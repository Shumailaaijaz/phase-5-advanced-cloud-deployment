'use client';

// Spec-006: T027-T028 - MessageBubble component with Markdown rendering

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/types/chat';
import { ToolBadge } from './ToolBadge';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex items-start gap-3 px-4 py-2 ${isUser ? 'justify-end' : 'justify-start'}`}
      role="article"
      aria-label={isUser ? 'You said' : 'Assistant said'}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'ml-auto rounded-br-sm bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]'
            : 'mr-auto rounded-bl-sm bg-[hsl(var(--muted))] text-[hsl(var(--foreground))]'
        }`}
      >
        {/* Tool badges for assistant messages */}
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1">
            {message.tool_calls.map((tc, idx) => (
              <ToolBadge key={idx} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Message content */}
        {isUser ? (
          <p className="whitespace-pre-wrap break-words text-sm">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none break-words text-sm prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-pre:my-2 prose-code:rounded prose-code:bg-black/10 prose-code:px-1 prose-code:py-0.5 prose-code:text-xs">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Streaming cursor */}
        {isStreaming && (
          <span className="inline-block h-4 w-1 animate-pulse bg-current" />
        )}
      </div>
    </div>
  );
}
