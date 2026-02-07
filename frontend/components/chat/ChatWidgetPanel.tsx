'use client';

import { useRouter } from 'next/navigation';
import { Maximize2, X } from 'lucide-react';
import { useChatContext } from './ChatProvider';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ErrorBanner } from './ErrorBanner';
import { EmptyState } from './EmptyState';
import { LoadingState } from './LoadingState';

interface ChatWidgetPanelProps {
  onClose: () => void;
}

export function ChatWidgetPanel({ onClose }: ChatWidgetPanelProps) {
  const router = useRouter();
  const { messages, isStreaming, error, clearError, sendMessage } = useChatContext();

  const handleExpand = () => {
    onClose();
    router.push('/chat');
  };

  return (
    <div className="fixed bottom-24 right-6 z-50 flex flex-col bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-[400px] h-[520px] max-sm:inset-0 max-sm:w-full max-sm:h-full max-sm:rounded-none max-sm:bottom-0 max-sm:right-0 animate-widget-enter overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-2xl max-sm:rounded-t-none">
        <h2 className="text-sm font-semibold">AI Assistant</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={handleExpand}
            aria-label="Expand to full page"
            className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
          >
            <Maximize2 size={16} />
          </button>
          <button
            onClick={onClose}
            aria-label="Close chat"
            className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {error && (
          <ErrorBanner message={error} onDismiss={clearError} />
        )}
        {messages.length === 0 && !isStreaming ? (
          <EmptyState />
        ) : (
          <MessageList messages={messages} isStreaming={isStreaming} />
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700">
        <ChatInput onSend={sendMessage} isDisabled={isStreaming} />
      </div>
    </div>
  );
}
