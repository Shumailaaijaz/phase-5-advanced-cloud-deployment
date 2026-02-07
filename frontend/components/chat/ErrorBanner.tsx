'use client';

// Spec-006: T045-T049, T105 - ErrorBanner with i18n

import { useLanguageContext } from './LanguageProvider';
import { CHAT_ERROR_COPY } from '@/i18n/chat';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorBanner({ message, onRetry, onDismiss }: ErrorBannerProps) {
  const { t } = useLanguageContext();
  const errorCopy = t(CHAT_ERROR_COPY);

  return (
    <div className="mx-4 my-2 flex items-center gap-3 rounded-xl border border-[hsl(var(--destructive))]/20 bg-[hsl(var(--destructive))]/5 px-4 py-3">
      <span className="text-sm text-[hsl(var(--destructive))]">{message}</span>
      <div className="ml-auto flex gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="rounded-lg bg-[hsl(var(--destructive))] px-3 py-1 text-xs font-medium text-[hsl(var(--destructive-foreground))] transition-colors hover:opacity-90"
          >
            {errorCopy.retryButton}
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="rounded-lg px-3 py-1 text-xs text-[hsl(var(--muted-foreground))] transition-colors hover:bg-[hsl(var(--muted))]"
          >
            {errorCopy.dismiss}
          </button>
        )}
      </div>
    </div>
  );
}
