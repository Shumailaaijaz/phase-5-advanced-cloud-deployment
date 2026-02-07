'use client';

// Spec-006: useLanguage hook - re-exports LanguageContext for convenience
import { useLanguageContext } from '@/components/chat/LanguageProvider';

export const useLanguage = useLanguageContext;
