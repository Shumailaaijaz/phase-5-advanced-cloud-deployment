'use client';

// Spec-006: T096-T099 - LanguageProvider with localStorage persistence

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import type { Language, LanguageState, LanguageActions } from '@/types/chat';
import { getTranslator } from '@/i18n/chat';

// ============================================================================
// Context
// ============================================================================

interface LanguageContextValue extends LanguageState, LanguageActions {
  t: ReturnType<typeof getTranslator>;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

const STORAGE_KEY = 'chat_ui_language';

function getDirection(lang: Language): 'ltr' | 'rtl' {
  return lang === 'ur' ? 'rtl' : 'ltr';
}

// ============================================================================
// Provider
// ============================================================================

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY) as Language | null;
      if (stored && ['en', 'ur', 'ur-RM'].includes(stored)) {
        setLanguageState(stored);
      }
    }
  }, []);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, lang);
    }
  }, []);

  const direction = getDirection(language);
  const t = getTranslator(language);

  const value: LanguageContextValue = {
    language,
    direction,
    setLanguage,
    t,
  };

  return (
    <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useLanguageContext(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguageContext must be used within a LanguageProvider');
  }
  return context;
}
