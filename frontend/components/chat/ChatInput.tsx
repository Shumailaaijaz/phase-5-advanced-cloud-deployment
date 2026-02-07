'use client';

// Spec-006: T030-T032 - ChatInput with Enter to send, Shift+Enter for newline

import { useState, useRef, useCallback, type KeyboardEvent } from 'react';
import { useLanguageContext } from './LanguageProvider';
import { CHAT_INPUT_COPY } from '@/i18n/chat';

interface ChatInputProps {
  onSend: (content: string) => void;
  isDisabled: boolean;
}

export function ChatInput({ onSend, isDisabled }: ChatInputProps) {
  const { t } = useLanguageContext();
  const inputCopy = t(CHAT_INPUT_COPY);
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isDisabled) return;

    onSend(trimmed);
    setValue('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, isDisabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setValue(e.target.value);

      // Auto-resize textarea
      const textarea = e.target;
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    },
    []
  );

  return (
    <div className="border-t border-[hsl(var(--border))] bg-[hsl(var(--background))] px-4 py-3">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          placeholder={inputCopy.placeholder}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-4 py-3 text-sm text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Type a message"
        />
        <button
          onClick={handleSend}
          disabled={isDisabled || !value.trim()}
          className="rounded-xl bg-[hsl(var(--primary))] px-4 py-3 text-sm font-medium text-[hsl(var(--primary-foreground))] transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Send message"
        >
          {isDisabled ? inputCopy.sending : inputCopy.sendButton}
        </button>
      </div>
    </div>
  );
}
