import * as React from "react"

import { cn } from "@/lib/utils"

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline"
}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border border-transparent px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2",
        {
          "border-transparent bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-100":
            variant === "default",
          "border-transparent bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100":
            variant === "secondary",
          "border-transparent bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100":
            variant === "destructive",
          "text-gray-800 dark:text-gray-100 border-gray-200 dark:border-gray-700":
            variant === "outline",
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }