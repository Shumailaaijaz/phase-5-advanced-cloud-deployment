'use client';

// Spec-006: useChat hook - re-exports ChatContext for convenience
import { useChatContext } from '@/components/chat/ChatProvider';

export const useChat = useChatContext;
