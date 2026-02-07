'use client';

// Spec-006: T060 - useScrollPosition hook

import { useCallback, useRef } from 'react';

export function useScrollPosition() {
  const positions = useRef<Record<string, number>>({});

  const save = useCallback((key: string, position: number) => {
    positions.current[key] = position;
  }, []);

  const restore = useCallback((key: string): number | undefined => {
    return positions.current[key];
  }, []);

  return { save, restore };
}
