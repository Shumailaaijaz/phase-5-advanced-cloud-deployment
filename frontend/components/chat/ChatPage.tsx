'use client';

// Spec-006: T023 - ChatPage container component

import { useState } from 'react';
import { useChatContext } from './ChatProvider';
import { useLanguageContext } from './LanguageProvider';
import { ConversationListPanel } from './ConversationListPanel';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ErrorBanner } from './ErrorBanner';
import { LoadingState } from './LoadingState';
import { EmptyState } from './EmptyState';
import { LanguageSelector } from './LanguageSelector';
import { CHAT_UI_COPY } from '@/i18n/chat';

export function ChatPage() {
  const {
    conversationList,
    activeConversationId,
    messages,
    isLoading,
    isStreaming,
    error,
    scrollPositions,
    sendMessage,
    selectConversation,
    startNewConversation,
    retryLastMessage,
    clearError,
    saveScrollPosition,
    lastFailedMessage,
  } = useChatContext();

  const { direction, t } = useLanguageContext();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const savedScrollPosition = activeConversationId
    ? scrollPositions[activeConversationId]
    : undefined;

  const uiCopy = t(CHAT_UI_COPY);

  return (
    <div dir={direction} className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Header with title and language selector */}
      <div className="absolute right-4 top-1 z-20 flex items-center gap-3">
        <span className="hidden text-sm font-medium text-[hsl(var(--foreground))] sm:inline">
          {uiCopy.title}
        </span>
        <LanguageSelector />
      </div>

      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed left-4 top-20 z-20 rounded-lg bg-[hsl(var(--background))] p-2 shadow-md lg:hidden"
        aria-label="Toggle conversations"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      {/* Conversation sidebar */}
      <div
        className={`${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } fixed inset-y-0 left-0 top-16 z-10 transition-transform lg:relative lg:top-0 lg:translate-x-0`}
      >
        <ConversationListPanel
          conversations={conversationList}
          activeId={activeConversationId}
          onSelect={(id) => {
            selectConversation(id);
            setSidebarOpen(false);
          }}
          onNewChat={() => {
            startNewConversation();
            setSidebarOpen(false);
          }}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-[5] bg-black/20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main chat area */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Error banner */}
        {error && (
          <ErrorBanner
            message={error}
            onRetry={lastFailedMessage ? retryLastMessage : undefined}
            onDismiss={clearError}
          />
        )}

        {/* Chat content */}
        {isLoading && messages.length === 0 ? (
          <LoadingState />
        ) : messages.length === 0 && !activeConversationId ? (
          <EmptyState />
        ) : (
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            onScrollPositionChange={saveScrollPosition}
            savedScrollPosition={savedScrollPosition}
          />
        )}

        {/* Input */}
        <ChatInput onSend={sendMessage} isDisabled={isStreaming} />
      </main>
    </div>
  );
}
