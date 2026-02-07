'use client';

// Spec-006: T033, T104 - StreamingIndicator with i18n

import { useLanguageContext } from './LanguageProvider';
import { CHAT_SYSTEM_COPY } from '@/i18n/chat';

export function StreamingIndicator() {
  const { t } = useLanguageContext();
  const copy = t(CHAT_SYSTEM_COPY);

  return (
    <div className="flex items-start gap-3 px-4 py-2">
      <div className="mr-auto max-w-[80%] rounded-2xl rounded-bl-sm bg-[hsl(var(--muted))] px-4 py-3">
        <span
          className="text-sm text-[hsl(var(--muted-foreground))]"
          aria-live="polite"
          aria-busy="true"
        >
          {copy.assistantTyping}
        </span>
      </div>
    </div>
  );
}
