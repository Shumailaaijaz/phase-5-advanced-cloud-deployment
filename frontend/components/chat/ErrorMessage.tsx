'use client';

// Spec-006: T046 - ErrorMessage displayed as chat bubble

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="flex items-start gap-3 px-4 py-2">
      <div className="mr-auto max-w-[80%] rounded-2xl rounded-bl-sm border border-[hsl(var(--destructive))]/20 bg-[hsl(var(--destructive))]/5 px-4 py-3">
        <p className="text-sm text-[hsl(var(--destructive))]">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 text-xs font-medium text-[hsl(var(--destructive))] underline hover:no-underline"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
