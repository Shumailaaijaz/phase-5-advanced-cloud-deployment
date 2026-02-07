// Spec-006: Frontend Chat UI API Client
// Communicates with Chat API (Spec-003)

import type {
  ChatRequest,
  ChatResponse,
  ConversationDetail,
  ConversationListResponse,
  ToolCall,
} from '@/types/chat';

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom error class for Chat API errors.
 * Provides user-friendly messages for display.
 */
export class ChatAPIError extends Error {
  code: string;
  statusCode: number;
  userMessage: string;

  constructor(code: string, statusCode: number, userMessage: string) {
    super(userMessage);
    this.name = 'ChatAPIError';
    this.code = code;
    this.statusCode = statusCode;
    this.userMessage = userMessage;
  }
}

/**
 * Map HTTP status codes and error codes to user-friendly messages.
 */
const ERROR_MESSAGE_MAP: Record<string, string> = {
  invalid_message: 'Please enter a valid message.',
  message_too_long: 'Your message is too long. Please shorten it.',
  unauthorized: 'Please sign in to continue.',
  forbidden: "You don't have access to this conversation.",
  conversation_not_found: "This conversation couldn't be found.",
  server_error: 'Something went wrong. Please try again.',
  network_error: "Couldn't connect. Please check your internet.",
  timeout: 'The request took too long. Please try again.',
};

function getErrorMessage(code: string, statusCode: number): string {
  if (ERROR_MESSAGE_MAP[code]) {
    return ERROR_MESSAGE_MAP[code];
  }

  // Fallback based on status code
  if (statusCode === 400) return 'Invalid request. Please try again.';
  if (statusCode === 401) return 'Please sign in to continue.';
  if (statusCode === 403) return "You don't have access to this resource.";
  if (statusCode === 404) return 'Resource not found.';
  if (statusCode >= 500) return 'Something went wrong. Please try again.';

  return 'An unexpected error occurred.';
}

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
const REQUEST_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // Exponential backoff

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get auth token from Better Auth session.
 */
async function getAuthToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null;

  // Try localStorage token set at login
  const token = localStorage.getItem('token');
  if (token) return token;

  // Better Auth uses cookie-based sessions — the token is sent
  // automatically via credentials: 'include' on fetch requests.
  // Return null here; the cookie handles auth.
  return null;
}

/**
 * Sleep for a specified duration.
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Make a fetch request with timeout.
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number = REQUEST_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ChatAPIError('timeout', 0, ERROR_MESSAGE_MAP.timeout);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Make an API request with retry logic.
 */
async function apiRequest<T>(
  url: string,
  options: RequestInit,
  retryCount: number = 0
): Promise<T> {
  const token = await getAuthToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetchWithTimeout(url, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorCode = errorData.error || 'server_error';
      const userMessage = getErrorMessage(errorCode, response.status);

      // Retry on 5xx errors (once)
      if (response.status >= 500 && retryCount < 1) {
        await sleep(1000);
        return apiRequest<T>(url, options, retryCount + 1);
      }

      throw new ChatAPIError(errorCode, response.status, userMessage);
    }

    return response.json();
  } catch (error) {
    // Handle network errors with retry
    if (
      error instanceof TypeError &&
      error.message.includes('fetch') &&
      retryCount < MAX_RETRIES
    ) {
      await sleep(RETRY_DELAYS[retryCount] || 4000);
      return apiRequest<T>(url, options, retryCount + 1);
    }

    // Re-throw ChatAPIError as-is
    if (error instanceof ChatAPIError) {
      throw error;
    }

    // Wrap other errors
    throw new ChatAPIError(
      'network_error',
      0,
      ERROR_MESSAGE_MAP.network_error
    );
  }
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Send a chat message and receive assistant response.
 *
 * @param userId - The authenticated user's ID
 * @param message - The message text to send
 * @param conversationId - Optional conversation ID to continue
 * @returns ChatResponse with assistant reply and tool calls
 */
export async function sendMessage(
  userId: string,
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  const body: ChatRequest = {
    message,
    ...(conversationId && { conversation_id: conversationId }),
  };

  return apiRequest<ChatResponse>(
    `${API_BASE_URL}/api/${userId}/chat`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    }
  );
}

/**
 * Get all conversations for a user.
 *
 * @param userId - The authenticated user's ID
 * @param options - Pagination options
 * @returns List of conversation summaries
 */
export async function listConversations(
  userId: string,
  options?: { limit?: number; offset?: number }
): Promise<ConversationListResponse> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.offset) params.set('offset', String(options.offset));

  const queryString = params.toString();
  const url = `${API_BASE_URL}/api/${userId}/conversations${queryString ? `?${queryString}` : ''}`;

  return apiRequest<ConversationListResponse>(url, { method: 'GET' });
}

/**
 * Get full conversation with all messages.
 *
 * @param userId - The authenticated user's ID
 * @param conversationId - The conversation to fetch
 * @returns Full conversation with messages
 */
export async function getConversation(
  userId: string,
  conversationId: string
): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(
    `${API_BASE_URL}/api/${userId}/conversations/${conversationId}`,
    { method: 'GET' }
  );
}

// ============================================================================
// Tool Call Transformation
// ============================================================================

/**
 * Transform raw tool call data to display format.
 */
export function transformToolCall(
  toolName: string,
  parameters?: Record<string, unknown>,
  result?: { success: boolean; [key: string]: unknown }
): ToolCall {
  const status: ToolCall['status'] = result?.success === false ? 'error' : 'completed';

  // Generate human-readable summary based on tool name
  let summary = '';
  switch (toolName) {
    case 'add_task':
      summary = `Task '${parameters?.title || 'Untitled'}' created`;
      break;
    case 'list_tasks':
      summary = 'Tasks retrieved';
      break;
    case 'complete_task':
      summary = `Task marked as complete`;
      break;
    case 'delete_task':
      summary = `Task deleted`;
      break;
    case 'update_task':
      summary = `Task updated`;
      break;
    default:
      summary = `${toolName} completed`;
  }

  return {
    tool_name: toolName,
    status,
    summary,
    details: undefined,
  };
}
