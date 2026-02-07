'use client';

// Spec-006: T110, T112 - Loading skeleton

export function LoadingState() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-6" aria-label="Loading conversation" role="status">
      {/* Skeleton messages */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`h-12 animate-pulse rounded-2xl bg-[hsl(var(--muted))] ${
              i % 2 === 0 ? 'w-1/3' : 'w-2/3'
            }`}
          />
        </div>
      ))}
      <span className="sr-only">Loading messages...</span>
    </div>
  );
}
