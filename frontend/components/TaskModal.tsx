'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authClient } from "@/lib/auth-client"; 
import { X, Plus, Edit3 } from 'lucide-react';
import { toast } from 'sonner';
import { createApiClientWithAuth } from '@/lib/api-client';
import { isErrorResponse } from '@/lib/error-handler';

// 1. Apni banayi hui types file se Task import karein
import { Task } from '@/types/task';

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  // task optional hai kyunki "Create" ke waqt ye null hota hai
  task?: Task | null;
  onSave: (savedTask: Task) => void;
}

export default function TaskModal({ isOpen, onClose, task, onSave }: TaskModalProps) {
  const { data: session } = authClient.useSession();
  const user = session?.user;
  
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (task) {
        setTitle(task.title);
        setDescription(task.description || '');
      } else {
        setTitle('');
        setDescription('');
      }
    }
  }, [isOpen, task]);

  const authApiClient = createApiClientWithAuth(session);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      toast.error('Session expired. Please log in again.');
      router.push('/login');
      return;
    }

    setIsLoading(true);

    try {
      const userId = user.id;

      if (task && task.id) {
        // Update existing task
        const response = await authApiClient.put<Task>(
          `/api/${userId}/tasks/${task.id}`,
          { title, description }
        );

        if (isErrorResponse(response)) {
          handleApiError(response.error);
          return;
        }

        toast.success('Task updated successfully');
        onSave(response as Task); // Type cast for safety
      } else {
        // Create new task
        const response = await authApiClient.post<Task>(
          `/api/${userId}/tasks`,
          { title, description }
        );

        if (isErrorResponse(response)) {
          handleApiError(response.error);
          return;
        }

        toast.success('Task created successfully');
        onSave(response as Task);
      }

      handleClose(); // Reset and close
    } catch (err) {
      toast.error('Connection failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiError = (error: string) => {
    if (error === 'unauthorized') {
      toast.error('Session expired');
      router.push('/login');
    } else if (error === 'user_id_mismatch') {
      toast.error('Access denied');
      router.refresh();
    } else {
      toast.error(`Error: ${error}`);
    }
  };

  const handleClose = () => {
    setTitle('');
    setDescription('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {task ? 'Edit Task' : 'Create New Task'}
            </h2>
            <button onClick={handleClose} className="text-gray-400 hover:text-gray-500">
              <X className="h-5 w-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter task title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter task description (optional)"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleClose}
                disabled={isLoading}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center space-x-2 hover:bg-indigo-700"
              >
                {isLoading ? (
                   <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                ) : (
                  task ? <Edit3 className="h-4 w-4" /> : <Plus className="h-4 w-4" />
                )}
                <span>{task ? 'Update' : 'Create'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}