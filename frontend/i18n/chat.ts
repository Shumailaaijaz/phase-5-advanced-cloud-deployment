// Spec-006: i18n - All UI copy in en/ur/ur-RM

import type { Language } from '@/types/chat';

// ============================================================================
// Copy Dictionaries
// ============================================================================

export const CHAT_UI_COPY = {
  en: { title: 'AI Assistant', subtitle: 'Manage your tasks with natural language' },
  ur: { title: 'AI معاون', subtitle: 'قدرتی زبان میں اپنے کام کا نظم کریں' },
  'ur-RM': { title: 'AI Madad-gaar', subtitle: 'Apne kaam ko natural language mein manage karein' },
};

export const CHAT_INPUT_COPY = {
  en: { placeholder: 'Type a message...', sendButton: 'Send', sending: 'Sending...' },
  ur: { placeholder: '...پیغام لکھیں', sendButton: 'بھیجیں', sending: '...بھیج رہے ہیں' },
  'ur-RM': { placeholder: 'Message likhein...', sendButton: 'Bhejein', sending: 'Bhej rahe hain...' },
};

export const CHAT_SYSTEM_COPY = {
  en: {
    emptyState: 'Start a conversation to manage your tasks',
    loadingConversation: 'Loading...',
    assistantTyping: 'Assistant is typing...',
    welcome: 'Welcome to Todo Assistant!',
    trySaying: 'Manage your tasks with natural language. Try saying:',
    getStarted: 'Type a message below to get started.',
    conversations: 'Conversations',
    newChat: '+ New',
    noConversations: 'No conversations yet',
    messages: 'messages',
  },
  ur: {
    emptyState: 'اپنے کام کا نظم کرنے کے لیے بات شروع کریں',
    loadingConversation: '...لوڈ ہو رہا ہے',
    assistantTyping: '...معاون لکھ رہا ہے',
    welcome: '!ٹوڈو اسسٹنٹ میں خوش آمدید',
    trySaying: ':قدرتی زبان میں اپنے کام کا نظم کریں۔ کہہ کر دیکھیں',
    getStarted: '.نیچے پیغام لکھ کر شروع کریں',
    conversations: 'بات چیت',
    newChat: '+ نئی',
    noConversations: 'ابھی تک کوئی بات چیت نہیں',
    messages: 'پیغامات',
  },
  'ur-RM': {
    emptyState: 'Apne tasks manage karne ke liye baat shuru karein',
    loadingConversation: 'Load ho raha hai...',
    assistantTyping: 'Madad-gaar likh raha hai...',
    welcome: 'Todo Assistant mein khush aamdeed!',
    trySaying: 'Apne kaam ko natural language mein manage karein. Keh kar dekhein:',
    getStarted: 'Neeche message likh kar shuru karein.',
    conversations: 'Baat cheet',
    newChat: '+ Nayi',
    noConversations: 'Abhi tak koi baat cheet nahi',
    messages: 'messages',
  },
};

export const CHAT_ERROR_COPY = {
  en: {
    genericError: 'Something went wrong. Please try again.',
    networkError: 'Unable to connect. Check your connection.',
    retryButton: 'Retry',
    dismiss: 'Dismiss',
  },
  ur: {
    genericError: 'کچھ غلط ہو گیا۔ دوبارہ کوشش کریں۔',
    networkError: 'کنیکشن نہیں ہو سکا۔ اپنا کنیکشن چیک کریں۔',
    retryButton: 'دوبارہ کوشش',
    dismiss: 'بند کریں',
  },
  'ur-RM': {
    genericError: 'Kuch ghalat ho gaya. Dobara koshish karein.',
    networkError: 'Connection nahi ho saka. Apna connection check karein.',
    retryButton: 'Dobara koshish',
    dismiss: 'Band karein',
  },
};

export const TOOL_UI_COPY = {
  en: {
    add_task: 'Task Created',
    update_task: 'Task Updated',
    delete_task: 'Task Deleted',
    complete_task: 'Task Completed',
    list_tasks: 'Listing Tasks',
  },
  ur: {
    add_task: 'ٹاسک بنا دیا گیا',
    update_task: 'ٹاسک اپڈیٹ ہو گیا',
    delete_task: 'ٹاسک حذف ہو گیا',
    complete_task: 'ٹاسک مکمل ہو گیا',
    list_tasks: 'ٹاسک دکھا رہے ہیں',
  },
  'ur-RM': {
    add_task: 'Task ban gaya',
    update_task: 'Task update ho gaya',
    delete_task: 'Task delete ho gaya',
    complete_task: 'Task mukammal ho gaya',
    list_tasks: 'Tasks dikha rahe hain',
  },
};

// ============================================================================
// Helper Types
// ============================================================================

type CopyDictionary<T> = Record<Language, T>;

/**
 * Generic translation function factory.
 * Returns the correct language variant from a copy dictionary.
 */
export function getTranslator(language: Language) {
  return function t<T>(dictionary: CopyDictionary<T>): T {
    return dictionary[language];
  };
}
