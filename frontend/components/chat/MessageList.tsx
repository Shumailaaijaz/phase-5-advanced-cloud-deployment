'use client';

// Spec-006: T026, T029, T034 - MessageList with auto-scroll and streaming indicator

import { useRef, useEffect, useCallback } from 'react';
import type { Message } from '@/types/chat';
import { MessageBubble } from './MessageBubble';
import { StreamingIndicator } from './StreamingIndicator';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  onScrollPositionChange?: (position: number) => void;
  savedScrollPosition?: number;
}

export function MessageList({
  messages,
  isStreaming,
  onScrollPositionChange,
  savedScrollPosition,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isUserScrolledUp = useRef(false);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (!isUserScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming]);

  // Restore scroll position on conversation switch
  useEffect(() => {
    if (savedScrollPosition !== undefined && containerRef.current) {
      containerRef.current.scrollTop = savedScrollPosition;
    }
  }, [savedScrollPosition]);

  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check if user scrolled up
    const isAtBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 50;
    isUserScrolledUp.current = !isAtBottom;

    // Report scroll position for persistence
    onScrollPositionChange?.(container.scrollTop);
  }, [onScrollPositionChange]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto custom-scrollbar"
      onScroll={handleScroll}
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      <div className="flex flex-col py-4">
        {(messages ?? []).map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isStreaming && <StreamingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
