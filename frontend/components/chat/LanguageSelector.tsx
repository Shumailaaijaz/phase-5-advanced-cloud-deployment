'use client';

// Spec-006: T098, T107 - LanguageSelector dropdown

import type { Language } from '@/types/chat';
import { useLanguageContext } from './LanguageProvider';

const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: 'en', label: 'English' },
  { value: 'ur', label: 'اردو' },
  { value: 'ur-RM', label: 'Roman Urdu' },
];

export function LanguageSelector() {
  const { language, setLanguage } = useLanguageContext();

  return (
    <select
      value={language}
      onChange={(e) => setLanguage(e.target.value as Language)}
      className="rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-2 py-1 text-xs text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
      aria-label="Select language"
    >
      {LANGUAGE_OPTIONS.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
