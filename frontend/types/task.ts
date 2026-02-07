export interface Task {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  priority: string; // P1, P2, P3, P4
  due_date: string | null;
  user_id: number;
  created_at: string;
  updated_at: string;
  tags?: string[];
  recurrence_rule?: string | null;
  recurrence_depth?: number;
  reminder_minutes?: number | null;
  reminder_sent?: boolean;
}

export const PRIORITIES = [
  { value: "P1", label: "P1 - Critical", color: "bg-red-100 text-red-700 border-red-200" },
  { value: "P2", label: "P2 - High", color: "bg-orange-100 text-orange-700 border-orange-200" },
  { value: "P3", label: "P3 - Medium", color: "bg-blue-100 text-blue-700 border-blue-200" },
  { value: "P4", label: "P4 - Low", color: "bg-gray-100 text-gray-600 border-gray-200" },
] as const;

export const RECURRENCE_OPTIONS = [
  { value: "", label: "No Recurrence" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
] as const;

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case "P1": return "bg-red-100 text-red-700 border-red-200";
    case "P2": return "bg-orange-100 text-orange-700 border-orange-200";
    case "P3": return "bg-blue-100 text-blue-700 border-blue-200";
    case "P4": return "bg-gray-100 text-gray-600 border-gray-200";
    // Legacy support
    case "High": return "bg-red-100 text-red-600";
    case "Medium": return "bg-amber-100 text-amber-600";
    case "Low": return "bg-blue-100 text-blue-600";
    default: return "bg-gray-100 text-gray-600";
  }
}

export function getPriorityLabel(priority: string): string {
  switch (priority) {
    case "P1": return "P1";
    case "P2": return "P2";
    case "P3": return "P3";
    case "P4": return "P4";
    default: return priority;
  }
}

export const prioritySortOrder: Record<string, number> = {
  P1: 1, P2: 2, P3: 3, P4: 4,
  High: 1, Medium: 2, Low: 3,
};
