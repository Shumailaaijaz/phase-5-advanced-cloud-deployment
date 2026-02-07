// Chat types for Spec-006: AI Chatbot UI

// ============================================================================
// Language
// ============================================================================

export type Language = 'en' | 'ur' | 'ur-RM';

export interface LanguageState {
  language: Language;
  direction: 'ltr' | 'rtl';
}

export interface LanguageActions {
  setLanguage: (lang: Language) => void;
}

// ============================================================================
// Tool Calls
// ============================================================================

export interface ToolCall {
  tool_name: string;
  status: 'completed' | 'error' | 'pending';
  summary?: string;
  details?: string;
}

export const TOOL_DISPLAY_MAP: Record<string, { label: string; emoji: string }> = {
  add_task: { label: 'Task Created', emoji: '\u2705' },
  update_task: { label: 'Task Updated', emoji: '\u270F\uFE0F' },
  delete_task: { label: 'Task Deleted', emoji: '\uD83D\uDDD1\uFE0F' },
  complete_task: { label: 'Task Completed', emoji: '\u2611\uFE0F' },
  list_tasks: { label: 'Listing Tasks', emoji: '\uD83D\uDCCB' },
};

// ============================================================================
// Messages
// ============================================================================

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  tool_calls?: ToolCall[];
}

// ============================================================================
// Conversations
// ============================================================================

export interface ConversationSummary {
  id: string;
  title?: string;
  message_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationDetail {
  id: string;
  title?: string;
  messages: Message[];
  created_at: string;
  updated_at?: string;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
}

// ============================================================================
// Chat API
// ============================================================================

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  tool_calls?: ToolCall[];
}

// ============================================================================
// Chat State
// ============================================================================

export interface ChatState {
  activeConversationId: string | null;
  conversationList: ConversationSummary[];
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  scrollPositions: Record<string, number>;
  streamingBuffer: string;
  lastFailedMessage: string | null;
}

export interface ChatActions {
  sendMessage: (content: string) => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  startNewConversation: () => void;
  retryLastMessage: () => Promise<void>;
  clearError: () => void;
  saveScrollPosition: (position: number) => void;
  refreshConversations: () => Promise<void>;
}
