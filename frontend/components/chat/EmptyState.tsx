'use client';

// Spec-006: T111, T113, T103 - Empty state with i18n

import { useLanguageContext } from './LanguageProvider';
import { CHAT_SYSTEM_COPY } from '@/i18n/chat';

export function EmptyState() {
  const { t } = useLanguageContext();
  const copy = t(CHAT_SYSTEM_COPY);

  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <div className="max-w-md text-center">
        <h2 className="mb-3 text-xl font-semibold text-[hsl(var(--foreground))]">
          {copy.welcome}
        </h2>
        <p className="mb-6 text-sm text-[hsl(var(--muted-foreground))]">
          {copy.trySaying}
        </p>
        <ul className="space-y-2 text-left text-sm text-[hsl(var(--muted-foreground))]">
          <li className="rounded-lg bg-[hsl(var(--muted))] px-4 py-2">
            &quot;Add a task to buy groceries&quot;
          </li>
          <li className="rounded-lg bg-[hsl(var(--muted))] px-4 py-2">
            &quot;What&apos;s on my list?&quot;
          </li>
          <li className="rounded-lg bg-[hsl(var(--muted))] px-4 py-2">
            &quot;Mark &apos;call mom&apos; as done&quot;
          </li>
        </ul>
        <p className="mt-6 text-xs text-[hsl(var(--muted-foreground))]">
          {copy.getStarted}
        </p>
      </div>
    </div>
  );
}
