// Custom event system for task updates across components

export const TASK_UPDATED_EVENT = 'task-updated';

export interface TaskUpdatedDetail {
  action: 'add' | 'complete' | 'delete' | 'update';
  timestamp: number;
}

// Dispatch when a task is modified (from chatbot or anywhere)
export function dispatchTaskUpdated(action: TaskUpdatedDetail['action'] = 'add') {
  const event = new CustomEvent<TaskUpdatedDetail>(TASK_UPDATED_EVENT, {
    detail: { action, timestamp: Date.now() },
  });
  window.dispatchEvent(event);
}

// Hook to listen for task updates
export function onTaskUpdated(callback: (detail: TaskUpdatedDetail) => void): () => void {
  const handler = (event: Event) => {
    const customEvent = event as CustomEvent<TaskUpdatedDetail>;
    callback(customEvent.detail);
  };

  window.addEventListener(TASK_UPDATED_EVENT, handler);

  // Return cleanup function
  return () => window.removeEventListener(TASK_UPDATED_EVENT, handler);
}
