'use client';

// Spec-006: Frontend Chat UI - ChatProvider
// Central state management for chat functionality

import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import type {
  ChatState,
  ChatActions,
  Message,
  ConversationSummary,
} from '@/types/chat';
import {
  sendMessage as apiSendMessage,
  listConversations,
  getConversation,
  ChatAPIError,
} from '@/lib/api/chat';
import { dispatchTaskUpdated } from '@/lib/events/taskEvents';

// ============================================================================
// Context
// ============================================================================

interface ChatContextValue extends ChatState, ChatActions {}

const ChatContext = createContext<ChatContextValue | null>(null);

// ============================================================================
// Initial State
// ============================================================================

const initialState: ChatState = {
  activeConversationId: null,
  conversationList: [],
  messages: [],
  isLoading: false,
  isStreaming: false,
  error: null,
  scrollPositions: {},
  streamingBuffer: '',
  lastFailedMessage: null,
};

// ============================================================================
// Actions
// ============================================================================

type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_STREAMING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONVERSATIONS'; payload: ConversationSummary[] }
  | { type: 'SET_ACTIVE_CONVERSATION'; payload: string | null }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; updates: Partial<Message> } }
  | { type: 'SAVE_SCROLL_POSITION'; payload: { conversationId: string; position: number } }
  | { type: 'SET_STREAMING_BUFFER'; payload: string }
  | { type: 'SET_LAST_FAILED_MESSAGE'; payload: string | null }
  | { type: 'CLEAR_ERROR' }
  | { type: 'START_NEW_CONVERSATION' };

// ============================================================================
// Reducer
// ============================================================================

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_STREAMING':
      return { ...state, isStreaming: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'SET_CONVERSATIONS':
      return { ...state, conversationList: action.payload ?? [] };

    case 'SET_ACTIVE_CONVERSATION':
      return { ...state, activeConversationId: action.payload };

    case 'SET_MESSAGES':
      return { ...state, messages: action.payload ?? [] };

    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };

    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, ...action.payload.updates }
            : msg
        ),
      };

    case 'SAVE_SCROLL_POSITION':
      return {
        ...state,
        scrollPositions: {
          ...state.scrollPositions,
          [action.payload.conversationId]: action.payload.position,
        },
      };

    case 'SET_STREAMING_BUFFER':
      return { ...state, streamingBuffer: action.payload };

    case 'SET_LAST_FAILED_MESSAGE':
      return { ...state, lastFailedMessage: action.payload };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'START_NEW_CONVERSATION':
      return {
        ...state,
        activeConversationId: null,
        messages: [],
        error: null,
      };

    default:
      return state;
  }
}

// ============================================================================
// Provider Props
// ============================================================================

interface ChatProviderProps {
  children: ReactNode;
  userId: string;
  initialConversationId?: string;
}

// ============================================================================
// Provider Component
// ============================================================================

export function ChatProvider({
  children,
  userId,
  initialConversationId,
}: ChatProviderProps) {
  const [state, dispatch] = useReducer(chatReducer, {
    ...initialState,
    activeConversationId: initialConversationId || null,
  });

  // -------------------------------------------------------------------------
  // Load conversations on mount
  // -------------------------------------------------------------------------
  const refreshConversations = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const response = await listConversations(userId);
      dispatch({ type: 'SET_CONVERSATIONS', payload: response?.conversations ?? [] });
    } catch (error) {
      const message =
        error instanceof ChatAPIError
          ? error.userMessage
          : 'Failed to load conversations';
      dispatch({ type: 'SET_ERROR', payload: message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [userId]);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  // -------------------------------------------------------------------------
  // Load messages when active conversation changes
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!state.activeConversationId) {
      dispatch({ type: 'SET_MESSAGES', payload: [] });
      return;
    }

    const loadMessages = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const conversation = await getConversation(userId, state.activeConversationId!);
        dispatch({ type: 'SET_MESSAGES', payload: conversation?.messages ?? [] });
      } catch (error) {
        const message =
          error instanceof ChatAPIError
            ? error.userMessage
            : 'Failed to load messages';
        dispatch({ type: 'SET_ERROR', payload: message });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    loadMessages();
  }, [state.activeConversationId, userId]);

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      // Clear any previous errors
      dispatch({ type: 'CLEAR_ERROR' });

      // Create optimistic user message
      const tempUserMessageId = `temp-${Date.now()}`;
      const userMessage: Message = {
        id: tempUserMessageId,
        role: 'user',
        content: content.trim(),
        created_at: new Date().toISOString(),
      };

      // Add user message optimistically
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SET_STREAMING', payload: true });
      dispatch({ type: 'SET_LAST_FAILED_MESSAGE', payload: null });

      try {
        const response = await apiSendMessage(
          userId,
          content.trim(),
          state.activeConversationId || undefined
        );

        // Update user message with real ID
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: { id: tempUserMessageId, updates: { id: response.user_message_id } },
        });

        // Add assistant message
        const assistantMessage: Message = {
          id: response.assistant_message_id,
          role: 'assistant',
          content: response.response,
          created_at: new Date().toISOString(),
          tool_calls: response.tool_calls,
        };
        dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

        // Notify dashboard if task tools were used
        if (response.tool_calls && response.tool_calls.length > 0) {
          const taskAction = response.tool_calls[0]?.tool_name?.includes('delete')
            ? 'delete'
            : response.tool_calls[0]?.tool_name?.includes('complete')
            ? 'complete'
            : response.tool_calls[0]?.tool_name?.includes('update')
            ? 'update'
            : 'add';
          dispatchTaskUpdated(taskAction);
        }

        // Update active conversation if this was a new conversation
        if (!state.activeConversationId && response.conversation_id) {
          dispatch({ type: 'SET_ACTIVE_CONVERSATION', payload: response.conversation_id });
          // Refresh conversation list to include new conversation
          await refreshConversations();
        }
      } catch (error) {
        const message =
          error instanceof ChatAPIError
            ? error.userMessage
            : 'Failed to send message';
        dispatch({ type: 'SET_ERROR', payload: message });
        dispatch({ type: 'SET_LAST_FAILED_MESSAGE', payload: content.trim() });

        // Remove the optimistic message on error
        dispatch({
          type: 'SET_MESSAGES',
          payload: state.messages.filter(m => m.id !== tempUserMessageId),
        });
      } finally {
        dispatch({ type: 'SET_STREAMING', payload: false });
      }
    },
    [userId, state.activeConversationId, state.messages, refreshConversations]
  );

  const selectConversation = useCallback(
    async (conversationId: string) => {
      // Save current scroll position before switching
      if (state.activeConversationId) {
        // Scroll position will be saved by the MessageList component
      }

      dispatch({ type: 'SET_ACTIVE_CONVERSATION', payload: conversationId });
    },
    [state.activeConversationId]
  );

  const startNewConversation = useCallback(() => {
    dispatch({ type: 'START_NEW_CONVERSATION' });
  }, []);

  const retryLastMessage = useCallback(async () => {
    if (state.lastFailedMessage) {
      await sendMessage(state.lastFailedMessage);
    }
  }, [state.lastFailedMessage, sendMessage]);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const saveScrollPosition = useCallback(
    (position: number) => {
      if (state.activeConversationId) {
        dispatch({
          type: 'SAVE_SCROLL_POSITION',
          payload: { conversationId: state.activeConversationId, position },
        });
      }
    },
    [state.activeConversationId]
  );

  // -------------------------------------------------------------------------
  // Context Value
  // -------------------------------------------------------------------------

  const value: ChatContextValue = {
    ...state,
    sendMessage,
    selectConversation,
    startNewConversation,
    retryLastMessage,
    clearError,
    saveScrollPosition,
    refreshConversations,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

// ============================================================================
// Hook
// ============================================================================

export function useChatContext(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}
