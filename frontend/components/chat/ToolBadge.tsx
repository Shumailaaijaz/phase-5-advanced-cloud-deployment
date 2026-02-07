'use client';

// Spec-006: T035-T039 - ToolBadge with expandable details

import { useState } from 'react';
import type { ToolCall } from '@/types/chat';
import { TOOL_DISPLAY_MAP } from '@/types/chat';
import { useLanguageContext } from './LanguageProvider';
import { TOOL_UI_COPY } from '@/i18n/chat';

interface ToolBadgeProps {
  toolCall: ToolCall;
}

export function ToolBadge({ toolCall }: ToolBadgeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { t } = useLanguageContext();
  const toolCopy = t(TOOL_UI_COPY);

  const fallbackDisplay = TOOL_DISPLAY_MAP[toolCall.tool_name] || {
    label: toolCall.tool_name,
    emoji: '🔧',
  };

  // Use i18n label if available, fallback to TOOL_DISPLAY_MAP
  const localizedLabel = (toolCopy as Record<string, string>)[toolCall.tool_name] || fallbackDisplay.label;
  const display = { ...fallbackDisplay, label: localizedLabel };

  const hasDetails = toolCall.summary || toolCall.details;

  return (
    <div className="inline-block">
      <button
        onClick={() => hasDetails && setIsExpanded(!isExpanded)}
        className={`inline-flex items-center gap-1 rounded-full bg-[hsl(var(--secondary))]/50 px-2 py-1 text-xs text-[hsl(var(--secondary-foreground))] transition-colors ${
          hasDetails ? 'cursor-pointer hover:bg-[hsl(var(--secondary))]/70' : 'cursor-default'
        } ${toolCall.status === 'error' ? 'bg-[hsl(var(--destructive))]/10 text-[hsl(var(--destructive))]' : ''}`}
        aria-expanded={hasDetails ? isExpanded : undefined}
        aria-label={`${display.emoji} ${display.label}`}
      >
        <span>{display.emoji}</span>
        <span>{display.label}</span>
        {hasDetails && (
          <span className="text-[10px]">{isExpanded ? '▲' : '▼'}</span>
        )}
      </button>
      {isExpanded && hasDetails && (
        <div className="mt-1 rounded-lg bg-[hsl(var(--secondary))]/30 px-3 py-2 text-xs text-[hsl(var(--muted-foreground))]">
          {toolCall.summary}
          {toolCall.details && (
            <div className="mt-1 border-t border-[hsl(var(--border))] pt-1 text-[10px] opacity-70">
              {toolCall.details}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
