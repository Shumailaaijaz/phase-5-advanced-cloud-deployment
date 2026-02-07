'use client';

import { ChatProvider } from '@/components/chat/ChatProvider';
import { ChatPage } from '@/components/chat/ChatPage';
import { LanguageProvider } from '@/components/chat/LanguageProvider';
import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

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

function ChatContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const conversationId = searchParams.get('conversation') || undefined;
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const id = getUserIdFromToken();
    if (!id) {
      router.push('/login');
      return;
    }
    setUserId(id);
  }, [router]);

  if (!userId) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  return (
    <LanguageProvider>
      <ChatProvider userId={userId} initialConversationId={conversationId}>
        <ChatPage />
      </ChatProvider>
    </LanguageProvider>
  );
}

export default function ChatRoute() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading...</div>}>
      <ChatContent />
    </Suspense>
  );
}
