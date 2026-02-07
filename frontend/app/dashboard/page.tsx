"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { toast } from "sonner";
import { onTaskUpdated } from "@/lib/events/taskEvents";
import { Task, PRIORITIES, RECURRENCE_OPTIONS, getPriorityColor, getPriorityLabel, prioritySortOrder } from "@/types/task";
import Image from "next/image";
import {
  Trash2, CheckCircle2, Circle, Search, ClipboardList,
  Pencil, Calendar, Plus, Sparkles, TrendingUp,
  Tag, Repeat, Bell, X
} from "lucide-react";

export default function Dashboard() {
  const router = useRouter();
  const [taskTitle, setTaskTitle] = useState("");
  const [priority, setPriority] = useState("P3");
  const [dueDate, setDueDate] = useState("");
  const [tags, setTags] = useState("");
  const [recurrenceRule, setRecurrenceRule] = useState("");
  const [reminderMinutes, setReminderMinutes] = useState("");
  const [filter, setFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [todos, setTodos] = useState<Task[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return router.push("/login");
    try {
      const payload = JSON.parse(window.atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      setUserId(payload.sub || payload.user_id);
    } catch (e) { router.push("/login"); }
  }, [router]);

  const fetchTodos = useCallback(async () => {
    if (!userId) return;
    const token = localStorage.getItem("token");
    const params = new URLSearchParams();
    if (searchQuery) params.set("search", searchQuery);
    if (priorityFilter) params.set("priority", priorityFilter);
    if (tagFilter) params.set("tag", tagFilter);
    if (filter === "Pending") params.set("completed", "false");
    if (filter === "Completed") params.set("completed", "true");

    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/${userId}/tasks?${params.toString()}`;
    const res = await fetch(url, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) setTodos(await res.json());
    setLoading(false);
  }, [userId, searchQuery, priorityFilter, tagFilter, filter]);

  useEffect(() => { if (userId) fetchTodos(); }, [userId, fetchTodos]);

  useEffect(() => {
    const cleanup = onTaskUpdated((detail) => {
      fetchTodos();
      if (detail.action === 'add') toast.success("Task added via chatbot!");
      else if (detail.action === 'complete') toast.success("Task completed via chatbot!");
      else if (detail.action === 'delete') toast.info("Task deleted via chatbot");
      else toast.success("Task updated via chatbot!");
    });
    return cleanup;
  }, [fetchTodos]);

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;
    const token = localStorage.getItem("token");

    const body: any = {
      title: taskTitle,
      description: "",
      completed: false,
      priority: priority,
    };
    if (dueDate) body.due_date = dueDate;
    if (tags.trim()) body.tags = tags.split(",").map(t => t.trim().toLowerCase()).filter(Boolean);
    if (recurrenceRule) body.recurrence_rule = recurrenceRule;
    if (reminderMinutes) body.reminder_minutes = parseInt(reminderMinutes);

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/${userId}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify(body)
    });
    if (res.ok) {
      setTaskTitle(""); setDueDate(""); setPriority("P3"); setTags(""); setRecurrenceRule(""); setReminderMinutes("");
      setShowAddForm(false);
      fetchTodos();
      toast.success("Task Added!");
    }
  };

  const handleDelete = async (taskId: string | number) => {
    const token = localStorage.getItem("token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/${userId}/tasks/${taskId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) { fetchTodos(); toast.error("Task Deleted"); }
  };

  const handleToggle = async (taskId: string | number) => {
    const token = localStorage.getItem("token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/${userId}/tasks/${taskId}/toggle`, {
      method: "PATCH",
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) fetchTodos();
  };

  const handleUpdate = async (taskId: string | number, currentTitle: string) => {
    const newTitle = prompt("Edit your task title:", currentTitle);
    if (newTitle === null || newTitle.trim() === "" || newTitle === currentTitle) return;
    const token = localStorage.getItem("token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/${userId}/tasks/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ title: newTitle.trim() })
    });
    if (res.ok) { fetchTodos(); toast.success("Task updated!"); }
  };

  const sortedTodos = [...todos].sort((a, b) =>
    (prioritySortOrder[a.priority] || 3) - (prioritySortOrder[b.priority] || 3)
  );

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch { return dateStr; }
  };

  const progressPercent = todos.length > 0 ? Math.round((todos.filter(t => t.completed).length / todos.length) * 100) : 0;
  const completedCount = todos.filter(t => t.completed).length;
  const pendingCount = todos.filter(t => !t.completed).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-indigo-100/40 to-purple-100/40 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-green-100/40 to-emerald-100/40 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

      <div className="absolute inset-0 opacity-[0.03] pointer-events-none">
        <Image src="/hero-image-h2p2.jpeg" alt="" fill className="object-cover" />
      </div>

      <div className="relative z-10 py-8 px-4 mt-16">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="relative w-[140px] h-[45px] drop-shadow-lg">
                <Image
                  src="/logoh2p2.jpeg"
                  alt="evoToDo Logo"
                  fill
                  className="object-contain rounded-xl"
                />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Today&apos;s Mission</h1>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-4 border border-white shadow-lg shadow-gray-100/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
                  <ClipboardList size={18} className="text-indigo-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{todos.length}</p>
                  <p className="text-xs text-gray-500 font-medium">Total</p>
                </div>
              </div>
            </div>
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-4 border border-white shadow-lg shadow-gray-100/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                  <Circle size={18} className="text-amber-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{pendingCount}</p>
                  <p className="text-xs text-gray-500 font-medium">Pending</p>
                </div>
              </div>
            </div>
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-4 border border-white shadow-lg shadow-gray-100/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
                  <CheckCircle2 size={18} className="text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{completedCount}</p>
                  <p className="text-xs text-gray-500 font-medium">Done</p>
                </div>
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 rounded-3xl p-6 mb-8 text-white shadow-2xl shadow-indigo-200/50 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl translate-x-1/2 -translate-y-1/2" />
            <div className="relative z-10">
              <div className="flex justify-between items-end mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp size={16} className="text-indigo-200" />
                    <p className="text-indigo-200 text-sm font-medium">Progress</p>
                  </div>
                  <h2 className="text-4xl font-bold">{progressPercent}%</h2>
                </div>
                <p className="text-indigo-200 text-sm">{completedCount} of {todos.length}</p>
              </div>
              <div className="w-full bg-white/20 rounded-full h-3">
                <div className="bg-gradient-to-r from-white to-indigo-100 h-3 rounded-full transition-all duration-700" style={{ width: `${progressPercent}%` }} />
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-2 mb-6">
            <div className="flex gap-2 bg-white/60 backdrop-blur-sm p-2 rounded-2xl border border-white shadow-sm">
              {["All", "Pending", "Completed"].map((tab) => (
                <button key={tab} onClick={() => setFilter(tab)}
                  className={`px-5 py-2 rounded-xl text-sm font-semibold transition-all ${
                    filter === tab ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg" : "text-gray-500 hover:bg-white/50"
                  }`}>
                  {tab}
                </button>
              ))}
            </div>

            {/* Priority filter */}
            <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-4 py-2.5 bg-white/70 border border-gray-200 rounded-xl text-sm font-semibold text-gray-600 outline-none">
              <option value="">All Priorities</option>
              {PRIORITIES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>

            {/* Tag filter */}
            <input type="text" placeholder="Filter by tag..." value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value.toLowerCase())}
              className="px-4 py-2.5 bg-white/70 border border-gray-200 rounded-xl text-sm outline-none w-32" />
          </div>

          {/* Search + Add */}
          <div className="space-y-4 mb-6">
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input type="text" placeholder="Search tasks (full-text)..."
                  value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 bg-white/70 backdrop-blur-sm border-2 border-gray-100 rounded-2xl outline-none focus:border-indigo-500 transition-all shadow-sm" />
              </div>
              <button onClick={() => setShowAddForm(!showAddForm)}
                className={`px-5 py-3.5 rounded-2xl font-semibold transition-all flex items-center gap-2 ${
                  showAddForm ? "bg-gray-200 text-gray-700" : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg"
                }`}>
                <Plus size={20} className={`transition-transform ${showAddForm ? "rotate-45" : ""}`} />
                <span className="hidden sm:inline">Add Task</span>
              </button>
            </div>

            {/* Add Task Form — Phase V */}
            {showAddForm && (
              <form onSubmit={handleAddTask} className="bg-white/80 backdrop-blur-xl p-5 rounded-3xl border border-white shadow-xl animate-in slide-in-from-top-2">
                <input type="text" placeholder="What needs to be done?" value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)} autoFocus
                  className="w-full px-4 py-3 text-lg font-medium outline-none bg-transparent border-b-2 border-gray-100 focus:border-indigo-500 transition-colors mb-4" />

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
                  {/* Priority */}
                  <select value={priority} onChange={(e) => setPriority(e.target.value)}
                    className="px-3 py-2.5 bg-gray-50 border-2 border-gray-100 rounded-xl text-sm font-semibold text-gray-600 outline-none focus:border-indigo-500">
                    {PRIORITIES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                  </select>

                  {/* Due Date */}
                  <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border-2 border-gray-100 rounded-xl">
                    <Calendar size={16} className="text-gray-400 flex-shrink-0" />
                    <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)}
                      className="bg-transparent text-sm font-semibold text-gray-600 outline-none w-full" />
                  </div>

                  {/* Recurrence */}
                  <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border-2 border-gray-100 rounded-xl">
                    <Repeat size={16} className="text-gray-400 flex-shrink-0" />
                    <select value={recurrenceRule} onChange={(e) => setRecurrenceRule(e.target.value)}
                      className="bg-transparent text-sm font-semibold text-gray-600 outline-none w-full">
                      {RECURRENCE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  {/* Tags */}
                  <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border-2 border-gray-100 rounded-xl">
                    <Tag size={16} className="text-gray-400 flex-shrink-0" />
                    <input type="text" placeholder="Tags (comma-separated)" value={tags}
                      onChange={(e) => setTags(e.target.value)}
                      className="bg-transparent text-sm text-gray-600 outline-none w-full" />
                  </div>

                  {/* Reminder */}
                  <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border-2 border-gray-100 rounded-xl">
                    <Bell size={16} className="text-gray-400 flex-shrink-0" />
                    <input type="number" placeholder="Remind (min before)" value={reminderMinutes}
                      onChange={(e) => setReminderMinutes(e.target.value)} min="0"
                      className="bg-transparent text-sm text-gray-600 outline-none w-full" />
                  </div>
                </div>

                <button type="submit"
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all active:scale-95 shadow-lg flex items-center justify-center gap-2">
                  <Sparkles size={16} />
                  Add Task
                </button>
              </form>
            )}
          </div>

          {/* Tasks List */}
          <div className="space-y-3">
            {loading ? (
              <div className="text-center py-16">
                <div className="inline-block w-10 h-10 border-3 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4" />
                <p className="text-gray-400 font-medium">Loading tasks...</p>
              </div>
            ) : sortedTodos.length === 0 ? (
              <div className="text-center py-16 bg-white/60 backdrop-blur-sm rounded-3xl border-2 border-dashed border-gray-200">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                  <ClipboardList size={28} className="text-indigo-500" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-1">No tasks found</h3>
                <p className="text-gray-400 text-sm">Add your first task to get started!</p>
              </div>
            ) : (
              sortedTodos.map((todo, index) => (
                <div key={todo.id}
                  className="group bg-white/80 backdrop-blur-sm p-4 rounded-2xl border border-white shadow-lg shadow-gray-100/50 hover:shadow-xl transition-all duration-300"
                  style={{ animationDelay: `${index * 50}ms` }}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 cursor-pointer flex-1" onClick={() => handleToggle(todo.id)}>
                      <div className={`mt-1 w-7 h-7 rounded-full flex items-center justify-center transition-all flex-shrink-0 ${
                        todo.completed ? "bg-gradient-to-br from-green-400 to-emerald-500 shadow-lg shadow-green-200" : "border-2 border-gray-300 group-hover:border-indigo-400"
                      }`}>
                        {todo.completed && <CheckCircle2 className="text-white" size={16} />}
                      </div>

                      <div className="flex flex-col gap-1.5 min-w-0">
                        {/* Priority + Due + Recurrence + Reminder badges */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-[10px] px-2.5 py-1 rounded-lg font-bold tracking-wide uppercase border ${getPriorityColor(todo.priority)}`}>
                            {getPriorityLabel(todo.priority)}
                          </span>
                          {todo.due_date && (
                            <span className="text-[11px] text-gray-500 font-medium flex items-center gap-1 bg-gray-100 px-2 py-1 rounded-lg">
                              <Calendar size={10} /> {formatDate(todo.due_date)}
                            </span>
                          )}
                          {todo.recurrence_rule && (
                            <span className="text-[10px] text-purple-600 font-semibold flex items-center gap-1 bg-purple-50 px-2 py-1 rounded-lg">
                              <Repeat size={10} /> {todo.recurrence_rule}
                            </span>
                          )}
                          {todo.reminder_minutes != null && todo.reminder_minutes > 0 && (
                            <span className="text-[10px] text-amber-600 font-semibold flex items-center gap-1 bg-amber-50 px-2 py-1 rounded-lg">
                              <Bell size={10} /> {todo.reminder_minutes}m
                            </span>
                          )}
                        </div>

                        {/* Title */}
                        <span className={`text-base font-semibold transition-all ${
                          todo.completed ? 'text-gray-400 line-through' : 'text-gray-800'
                        }`}>
                          {todo.title}
                        </span>

                        {/* Tags */}
                        {todo.tags && todo.tags.length > 0 && (
                          <div className="flex gap-1.5 flex-wrap">
                            {todo.tags.map((tag: string) => (
                              <span key={tag} className="text-[10px] px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-md font-medium">
                                #{tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button onClick={(e) => { e.stopPropagation(); handleUpdate(todo.id, todo.title); }}
                        className="p-2.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all">
                        <Pencil size={16} />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(todo.id); }}
                        className="p-2.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
