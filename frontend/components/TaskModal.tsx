'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authClient } from "@/lib/auth-client";
import { X, Plus, Edit3, Calendar, Tag, Repeat, Bell } from 'lucide-react';
import { toast } from 'sonner';
import { createApiClientWithAuth } from '@/lib/api-client';
import { isErrorResponse } from '@/lib/error-handler';
import { Task, PRIORITIES, RECURRENCE_OPTIONS } from '@/types/task';

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: Task | null;
  onSave: (savedTask: Task) => void;
}

export default function TaskModal({ isOpen, onClose, task, onSave }: TaskModalProps) {
  const { data: session } = authClient.useSession();
  const user = session?.user;
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('P3');
  const [dueDate, setDueDate] = useState('');
  const [tags, setTags] = useState('');
  const [recurrenceRule, setRecurrenceRule] = useState('');
  const [reminderMinutes, setReminderMinutes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (task) {
        setTitle(task.title);
        setDescription(task.description || '');
        setPriority(task.priority || 'P3');
        setDueDate(task.due_date ? task.due_date.split('T')[0] : '');
        setTags(task.tags ? task.tags.join(', ') : '');
        setRecurrenceRule(task.recurrence_rule || '');
        setReminderMinutes(task.reminder_minutes != null ? String(task.reminder_minutes) : '');
      } else {
        setTitle(''); setDescription(''); setPriority('P3'); setDueDate('');
        setTags(''); setRecurrenceRule(''); setReminderMinutes('');
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
      const body: any = { title, description, priority };
      if (dueDate) body.due_date = dueDate;
      if (tags.trim()) body.tags = tags.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
      if (recurrenceRule) body.recurrence_rule = recurrenceRule;
      if (reminderMinutes) body.reminder_minutes = parseInt(reminderMinutes);

      if (task && task.id) {
        const response = await authApiClient.put<Task>(`/api/${userId}/tasks/${task.id}`, body);
        if (isErrorResponse(response)) { handleApiError(response.error); return; }
        toast.success('Task updated successfully');
        onSave(response as Task);
      } else {
        const response = await authApiClient.post<Task>(`/api/${userId}/tasks`, body);
        if (isErrorResponse(response)) { handleApiError(response.error); return; }
        toast.success('Task created successfully');
        onSave(response as Task);
      }
      handleClose();
    } catch (err) {
      toast.error('Connection failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiError = (error: string) => {
    if (error === 'unauthorized') { toast.error('Session expired'); router.push('/login'); }
    else if (error === 'user_id_mismatch') { toast.error('Access denied'); router.refresh(); }
    else toast.error(`Error: ${error}`);
  };

  const handleClose = () => {
    setTitle(''); setDescription(''); setPriority('P3'); setDueDate('');
    setTags(''); setRecurrenceRule(''); setReminderMinutes('');
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
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter task title" />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Optional description" />
              </div>

              {/* Priority + Due Date row */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Priority</label>
                  <select value={priority} onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500">
                    {PRIORITIES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <Calendar size={14} /> Due Date
                  </label>
                  <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  <Tag size={14} /> Tags
                </label>
                <input type="text" value={tags} onChange={(e) => setTags(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="work, meeting, urgent (comma-separated)" />
              </div>

              {/* Recurrence + Reminder row */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <Repeat size={14} /> Recurrence
                  </label>
                  <select value={recurrenceRule} onChange={(e) => setRecurrenceRule(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500">
                    {RECURRENCE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <Bell size={14} /> Reminder
                  </label>
                  <input type="number" value={reminderMinutes} onChange={(e) => setReminderMinutes(e.target.value)}
                    min="0" placeholder="Minutes before"
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button type="button" onClick={handleClose} disabled={isLoading}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200">
                Cancel
              </button>
              <button type="submit" disabled={isLoading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center space-x-2 hover:bg-indigo-700">
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
