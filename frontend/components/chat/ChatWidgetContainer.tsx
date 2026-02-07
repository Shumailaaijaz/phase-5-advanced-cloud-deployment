'use client';

import React, { useEffect, useState } from 'react';
import { LanguageProvider } from './LanguageProvider';
import { ChatProvider } from './ChatProvider';
import { ChatWidgetPanel } from './ChatWidgetPanel';

interface ChatWidgetContainerProps {
  onClose: () => void;
}

// Error boundary to prevent widget crashes from breaking the whole page
class WidgetErrorBoundary extends React.Component<
  { children: React.ReactNode; onClose: () => void },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; onClose: () => void }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="fixed bottom-24 right-6 z-50 flex flex-col items-center justify-center bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-[400px] h-[520px] max-sm:inset-0 max-sm:w-full max-sm:h-full max-sm:rounded-none p-6 text-center">
          <p className="text-sm text-gray-600 mb-4">Chat could not load. Please try again.</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 mr-2"
          >
            Retry
          </button>
          <button
            onClick={this.props.onClose}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 mt-2"
          >
            Close
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function getUserIdFromToken(): string | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem('token');
  if (!token) return null;
  try {
    const payload = JSON.parse(
      window.atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))
    );
    return String(payload.sub || payload.user_id || '');
  } catch {
    return null;
  }
}

export function ChatWidgetContainer({ onClose }: ChatWidgetContainerProps) {
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    setUserId(getUserIdFromToken());
  }, []);

  if (!userId) return null;

  return (
    <WidgetErrorBoundary onClose={onClose}>
      <LanguageProvider>
        <ChatProvider userId={userId}>
          <ChatWidgetPanel onClose={onClose} />
        </ChatProvider>
      </LanguageProvider>
    </WidgetErrorBoundary>
  );
}
