'use client';

// Spec-006: T055-T062 - ConversationListPanel with conversation switching

import type { ConversationSummary } from '@/types/chat';

interface ConversationListPanelProps {
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export function ConversationListPanel({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  isOpen = true,
  onClose,
}: ConversationListPanelProps) {
  if (!isOpen) return null;

  return (
    <aside className="flex h-full w-64 flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--background))]">
      <div className="flex items-center justify-between border-b border-[hsl(var(--border))] px-4 py-3">
        <h2 className="text-sm font-semibold text-[hsl(var(--foreground))]">Conversations</h2>
        <div className="flex gap-1">
          <button
            onClick={onNewChat}
            className="rounded-lg px-3 py-1 text-xs font-medium text-[hsl(var(--primary))] transition-colors hover:bg-[hsl(var(--muted))]"
            aria-label="New conversation"
          >
            + New
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg px-2 py-1 text-xs text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] lg:hidden"
              aria-label="Close sidebar"
            >
              ✕
            </button>
          )}
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto custom-scrollbar">
        {conversations.length === 0 ? (
          <p className="p-4 text-xs text-[hsl(var(--muted-foreground))]">No conversations yet</p>
        ) : (
          <ul className="py-1">
            {conversations.map((conv) => (
              <li key={conv.id}>
                <button
                  onClick={() => onSelect(conv.id)}
                  className={`w-full px-4 py-3 text-left transition-colors ${
                    conv.id === activeId
                      ? 'bg-[hsl(var(--muted))] text-[hsl(var(--foreground))]'
                      : 'text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]/50'
                  }`}
                  aria-current={conv.id === activeId ? 'true' : undefined}
                >
                  <p className="truncate text-sm font-medium">
                    {conv.title || 'New Conversation'}
                  </p>
                  <p className="mt-0.5 text-xs opacity-60">
                    {conv.message_count} messages
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>
    </aside>
  );
}
