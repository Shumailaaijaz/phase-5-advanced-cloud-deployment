'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authClient } from "@/lib/auth-client";
import { Check, Square, Edit3, Trash2, AlertCircle, Calendar, Repeat, Bell } from 'lucide-react';
import { toast } from 'sonner';
import { createApiClientWithAuth } from '@/lib/api-client';
import { isErrorResponse } from '@/lib/error-handler';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import TaskModal from '@/components/TaskModal';
import { Task, getPriorityColor, getPriorityLabel } from '@/types/task';

interface TaskCardProps {
  task: Task;
  onTaskUpdate?: (updatedTask: Task) => void;
  onTaskDelete?: (taskId: string) => void;
}

export default function TaskCard({ task, onTaskUpdate, onTaskDelete }: TaskCardProps) {
  const { data: session } = authClient.useSession();
  const user = session?.user;
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [localTask, setLocalTask] = useState<Task>(task);

  const authApiClient = createApiClientWithAuth(session);

  useEffect(() => { setLocalTask(task); }, [task]);

  const toggleCompletion = async () => {
    if (!user) { toast.error('Session expired.'); router.push('/login'); return; }
    setIsLoading(true);
    try {
      const response = await authApiClient.patch<Partial<Task>>(`/api/${user.id}/tasks/${localTask.id}/complete`, {});
      if (isErrorResponse(response)) { handleApiError(response.error); return; }
      const updatedTask = { ...localTask, completed: !localTask.completed };
      setLocalTask(updatedTask);
      if (onTaskUpdate) onTaskUpdate(updatedTask);
      toast.success(`Task ${updatedTask.completed ? 'completed' : 'marked as incomplete'}`);
    } catch (err) { toast.error('Connection failed'); }
    finally { setIsLoading(false); }
  };

  const handleApiError = (error: string) => {
    if (error === 'unauthorized') { toast.error('Session expired'); router.push('/login'); }
    else if (error === 'user_id_mismatch') { toast.error('Access denied'); router.refresh(); }
    else toast.error(`Error: ${error}`);
  };

  const confirmDelete = async () => {
    if (!user) return;
    setIsDeleting(true);
    try {
      const response = await authApiClient.delete<null>(`/api/${user.id}/tasks/${localTask.id}`);
      if (isErrorResponse(response)) { handleApiError(response.error); return; }
      if (onTaskDelete) onTaskDelete(localTask.id);
      toast.success('Task deleted');
      setShowDeleteDialog(false);
    } catch (err) { toast.error('Connection failed'); }
    finally { setIsDeleting(false); }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return null;
    try {
      return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return dateString; }
  };

  return (
    <>
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center space-x-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Delete Task</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-300">Are you sure? This cannot be undone.</p>
            <div className="flex justify-end space-x-3 pt-4">
              <button onClick={() => setShowDeleteDialog(false)} className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded-md">Cancel</button>
              <button onClick={confirmDelete} disabled={isDeleting}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-md flex items-center space-x-2">
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      <Card className={`relative border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all ${
        localTask.completed ? 'bg-gray-50 dark:bg-gray-800/70 opacity-70' : 'bg-white dark:bg-gray-800'
      }`}>
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <button onClick={toggleCompletion} disabled={isLoading}
              className={`mt-1 flex-shrink-0 rounded border-2 ${
                localTask.completed ? 'border-indigo-500 bg-indigo-500' : 'border-gray-300 dark:border-gray-600'
              }`}>
              {localTask.completed ? <Check className="h-4 w-4 text-white" /> : <Square className="h-4 w-4 text-transparent" />}
            </button>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <h3 className={`text-sm font-medium ${localTask.completed ? 'text-gray-500 line-through' : 'text-gray-900 dark:text-white'}`}>
                  {localTask.title}
                </h3>
                <div className="flex items-center space-x-2">
                  <button onClick={() => setShowEditModal(true)} className="text-gray-400 hover:text-gray-600"><Edit3 className="h-4 w-4" /></button>
                  <button onClick={() => setShowDeleteDialog(true)} className="text-gray-400 hover:text-red-500"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>

              {localTask.description && (
                <p className={`text-sm mt-1 ${localTask.completed ? 'text-gray-400 line-through' : 'text-gray-500'}`}>
                  {localTask.description}
                </p>
              )}

              {/* Phase V badges */}
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                {/* Priority badge */}
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${getPriorityColor(localTask.priority)}`}>
                  {getPriorityLabel(localTask.priority)}
                </span>

                {/* Due date */}
                {localTask.due_date && (
                  <span className="text-[11px] text-gray-500 flex items-center gap-1">
                    <Calendar size={10} /> {formatDate(localTask.due_date)}
                  </span>
                )}

                {/* Recurrence */}
                {localTask.recurrence_rule && (
                  <span className="text-[10px] text-purple-600 flex items-center gap-1 bg-purple-50 px-1.5 py-0.5 rounded">
                    <Repeat size={10} /> {localTask.recurrence_rule}
                  </span>
                )}

                {/* Reminder */}
                {localTask.reminder_minutes != null && localTask.reminder_minutes > 0 && (
                  <span className="text-[10px] text-amber-600 flex items-center gap-1 bg-amber-50 px-1.5 py-0.5 rounded">
                    <Bell size={10} /> {localTask.reminder_minutes}m
                  </span>
                )}

                {localTask.completed && <Badge variant="secondary" className="text-xs">Completed</Badge>}
              </div>

              {/* Tags */}
              {localTask.tags && localTask.tags.length > 0 && (
                <div className="mt-1.5 flex gap-1 flex-wrap">
                  {localTask.tags.map((tag: string) => (
                    <span key={tag} className="text-[10px] px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded font-medium">#{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
          {isLoading && (
            <div className="absolute inset-0 bg-white/50 dark:bg-gray-800/50 flex items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
            </div>
          )}
        </CardContent>
      </Card>

      <TaskModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        task={localTask}
        onSave={(updatedTask) => {
          setLocalTask(updatedTask);
          if (onTaskUpdate) onTaskUpdate(updatedTask);
          setShowEditModal(false);
          toast.success('Task updated successfully');
        }}
      />
    </>
  );
}
