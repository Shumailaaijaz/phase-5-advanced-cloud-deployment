# Phase II Skills — Full-Stack Web Application

## Overview

Phase II transforms the console Todo application into a full-stack web system using Next.js (frontend) and FastAPI (backend). These skills are designed for AI agents to build upon Phase I foundations while introducing web, API, and persistence capabilities.

---

## 🎯 Core Skills Catalog

### 1. Next.js Component Skill

**Purpose**: Create reusable React/Next.js components with TypeScript

**Inputs**:
- `component_name`: Name of the component
- `props_schema`: TypeScript interface for props
- `component_type`: "client" | "server" | "hybrid"
- `styling`: "tailwind" | "css-modules" | "styled-components"

**Outputs**:
- `component_file`: Generated component code
- `types_file`: TypeScript types/interfaces
- `is_accessible`: Boolean (WCAG compliance check)

**Implementation Template**:
```typescript
// File: app/components/TaskList.tsx
// [Skill]: Next.js Component

/**
 * TaskList component displays a list of tasks.
 *
 * @component
 */

'use client'

import { Task } from '@/types'

interface TaskListProps {
  tasks: Task[]
  onTaskClick?: (id: number) => void
  showCompleted?: boolean
}

export default function TaskList({
  tasks,
  onTaskClick,
  showCompleted = true
}: TaskListProps) {
  const filteredTasks = showCompleted
    ? tasks
    : tasks.filter(t => !t.completed)

  return (
    <div className="space-y-2" role="list">
      {filteredTasks.map(task => (
        <TaskItem
          key={task.id}
          task={task}
          onClick={onTaskClick}
        />
      ))}
    </div>
  )
}
```

**Quality Standards**:
- TypeScript strict mode enabled
- Accessible markup (ARIA, semantic HTML)
- Client/Server component boundary clearly defined
- Tailwind CSS for styling consistency

---

### 2. API Route Skill

**Purpose**: Create Next.js API routes with proper error handling

**Inputs**:
- `route_path`: API endpoint path
- `http_method`: GET | POST | PUT | DELETE
- `request_schema`: Expected request body schema
- `response_schema`: Response data schema

**Outputs**:
- `route_file`: API route handler
- `validation_result`: Request validation status
- `error_handling`: Error response format

**Implementation Template**:
```typescript
// File: app/api/tasks/route.ts
// [Skill]: API Route

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const TaskCreateSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate input
    const validatedData = TaskCreateSchema.parse(body)

    // Call backend API
    const response = await fetch('http://localhost:8000/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validatedData),
    })

    if (!response.ok) {
      throw new Error('Backend API error')
    }

    const data = await response.json()

    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.errors },
        { status: 400 }
      )
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch('http://localhost:8000/api/tasks')
    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch tasks' },
      { status: 500 }
    )
  }
}
```

**Quality Standards**:
- Zod schema validation for all inputs
- Proper HTTP status codes
- Error responses follow RFC 7807 format
- Rate limiting considered

---

### 3. FastAPI Endpoint Skill

**Purpose**: Create FastAPI endpoints with Pydantic validation

**Inputs**:
- `endpoint_path`: API route path
- `http_method`: HTTPMethod enum
- `request_model`: Pydantic model for request
- `response_model`: Pydantic model for response

**Outputs**:
- `endpoint_code`: FastAPI route function
- `openapi_spec`: Generated OpenAPI documentation
- `test_cases`: Pytest test cases

**Implementation Template**:
```python
# File: app/api/routes/tasks.py
# [Skill]: FastAPI Endpoint

"""
Task API endpoints.

Provides RESTful API for task management.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Task creation request."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response model."""
    id: int
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    """
    Create a new task.

    Args:
        task: Task creation data

    Returns:
        Created task with ID

    Raises:
        HTTPException: If validation fails or creation error occurs
    """
    try:
        # Use Phase I logic (adapted for persistence)
        from app.services.task_service import TaskService

        service = TaskService()
        created_task = await service.create_task(
            title=task.title,
            description=task.description
        )

        return created_task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(completed: Optional[bool] = None):
    """
    List all tasks with optional filtering.

    Args:
        completed: Filter by completion status

    Returns:
        List of tasks
    """
    from app.services.task_service import TaskService

    service = TaskService()
    tasks = await service.list_tasks(completed=completed)

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """
    Get a single task by ID.

    Args:
        task_id: Task identifier

    Returns:
        Task details

    Raises:
        HTTPException: If task not found
    """
    from app.services.task_service import TaskService

    service = TaskService()
    task = await service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskCreate):
    """Update an existing task."""
    from app.services.task_service import TaskService

    service = TaskService()

    try:
        updated = await service.update_task(
            task_id=task_id,
            title=task.title,
            description=task.description
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    """Delete a task."""
    from app.services.task_service import TaskService

    service = TaskService()

    success = await service.delete_task(task_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
```

**Quality Standards**:
- Pydantic models for all I/O
- Async/await for database operations
- Proper HTTP status codes
- OpenAPI documentation auto-generated
- Follows REST conventions

---

### 4. Database Schema Skill

**Purpose**: Define database models with SQLModel/SQLAlchemy

**Inputs**:
- `model_name`: Database model name
- `fields`: Field definitions with types
- `relationships`: Foreign keys and relations
- `indexes`: Index definitions

**Outputs**:
- `model_file`: SQLModel class definition
- `migration_file`: Alembic migration script
- `validation_schema`: Pydantic schema for validation

**Implementation Template**:
```python
# File: app/models/task.py
# [Skill]: Database Schema

"""
Task database model.

SQLModel-based ORM model for tasks.
"""

from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import Optional


class Task(SQLModel, table=True):
    """
    Task model for persistent storage.

    Extends Phase I task logic with database persistence.
    """

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Phase II: Add user relationship (prepare for Phase III)
    # user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    # user: Optional["User"] = Relationship(back_populates="tasks")

    class Config:
        """Model configuration."""
        json_schema_extra = {
            "example": {
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False
            }
        }
```

**Migration Template**:
```python
# File: alembic/versions/001_create_tasks_table.py
# [Skill]: Database Migration

"""create tasks table

Revision ID: 001
Revises:
Create Date: 2024-01-07
"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tasks table."""
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create indexes
    op.create_index('ix_tasks_title', 'tasks', ['title'])
    op.create_index('ix_tasks_completed', 'tasks', ['completed'])


def downgrade() -> None:
    """Drop tasks table."""
    op.drop_index('ix_tasks_completed', table_name='tasks')
    op.drop_index('ix_tasks_title', table_name='tasks')
    op.drop_table('tasks')
```

**Quality Standards**:
- Explicit column types and constraints
- Proper indexes for query patterns
- Reversible migrations
- No data loss on rollback
- Foreign key constraints where applicable

---

### 5. Frontend Data Fetching Skill

**Purpose**: Implement client-side data fetching with SWR/React Query

**Inputs**:
- `api_endpoint`: Backend API URL
- `fetch_strategy`: "swr" | "react-query" | "fetch"
- `cache_config`: Cache revalidation settings
- `error_handling`: Error boundary strategy

**Outputs**:
- `hook_file`: Custom React hook
- `error_boundary`: Error handling component
- `loading_state`: Loading UI component

**Implementation Template**:
```typescript
// File: app/hooks/useTasks.ts
// [Skill]: Frontend Data Fetching

'use client'

import useSWR from 'swr'
import { Task } from '@/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

export function useTasks(completed?: boolean) {
  const queryParams = completed !== undefined
    ? `?completed=${completed}`
    : ''

  const { data, error, isLoading, mutate } = useSWR<Task[]>(
    `/api/tasks${queryParams}`,
    fetcher,
    {
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      refreshInterval: 30000, // 30 seconds
    }
  )

  return {
    tasks: data,
    isLoading,
    isError: error,
    mutate, // For optimistic updates
  }
}

export function useTask(id: number) {
  const { data, error, isLoading } = useSWR<Task>(
    id ? `/api/tasks/${id}` : null,
    fetcher
  )

  return {
    task: data,
    isLoading,
    isError: error,
  }
}

export async function createTask(title: string, description?: string) {
  const response = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Failed to create task')
  }

  return response.json()
}

export async function updateTask(
  id: number,
  updates: Partial<Task>
) {
  const response = await fetch(`/api/tasks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  })

  if (!response.ok) {
    throw new Error('Failed to update task')
  }

  return response.json()
}

export async function deleteTask(id: number) {
  const response = await fetch(`/api/tasks/${id}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error('Failed to delete task')
  }
}
```

**Quality Standards**:
- Automatic revalidation on window focus
- Optimistic UI updates
- Error retry logic
- TypeScript for all data shapes
- Loading and error states handled

---

### 6. Form Handling Skill

**Purpose**: Create forms with validation using React Hook Form + Zod

**Inputs**:
- `form_name`: Form identifier
- `schema`: Zod validation schema
- `submit_action`: Server action or API call
- `error_display`: Error UI strategy

**Outputs**:
- `form_component`: React component
- `validation_errors`: Field-level errors
- `submit_result`: Success/failure state

**Implementation Template**:
```typescript
// File: app/components/TaskForm.tsx
// [Skill]: Form Handling

'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'

const taskSchema = z.object({
  title: z.string()
    .min(1, 'Title is required')
    .max(200, 'Title must be 200 characters or less'),
  description: z.string()
    .max(1000, 'Description must be 1000 characters or less')
    .optional(),
})

type TaskFormData = z.infer<typeof taskSchema>

interface TaskFormProps {
  onSubmit: (data: TaskFormData) => Promise<void>
  initialData?: TaskFormData
  submitLabel?: string
}

export default function TaskForm({
  onSubmit,
  initialData,
  submitLabel = 'Create Task'
}: TaskFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
    defaultValues: initialData,
  })

  const onSubmitForm = async (data: TaskFormData) => {
    setIsSubmitting(true)
    setSubmitError(null)

    try {
      await onSubmit(data)
      reset()
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : 'Failed to submit form'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmitForm)}
      className="space-y-4"
    >
      <div>
        <label
          htmlFor="title"
          className="block text-sm font-medium"
        >
          Title *
        </label>
        <input
          id="title"
          type="text"
          {...register('title')}
          className="mt-1 block w-full rounded-md border p-2"
          aria-invalid={errors.title ? 'true' : 'false'}
          aria-describedby={errors.title ? 'title-error' : undefined}
        />
        {errors.title && (
          <p id="title-error" className="mt-1 text-sm text-red-600">
            {errors.title.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="description"
          className="block text-sm font-medium"
        >
          Description
        </label>
        <textarea
          id="description"
          {...register('description')}
          rows={3}
          className="mt-1 block w-full rounded-md border p-2"
          aria-invalid={errors.description ? 'true' : 'false'}
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">
            {errors.description.message}
          </p>
        )}
      </div>

      {submitError && (
        <div
          role="alert"
          className="rounded-md bg-red-50 p-4 text-red-800"
        >
          {submitError}
        </div>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
      >
        {isSubmitting ? 'Submitting...' : submitLabel}
      </button>
    </form>
  )
}
```

**Quality Standards**:
- Schema-based validation (Zod)
- Accessible form markup (labels, ARIA)
- Loading states during submission
- Error messages displayed inline
- Form reset after successful submit

---

### 7. Environment Configuration Skill

**Purpose**: Manage environment variables across frontend and backend

**Inputs**:
- `environment`: "development" | "test" | "production"
- `config_keys`: List of required config keys
- `validation_rules`: Validation for each key

**Outputs**:
- `env_file`: .env template
- `config_module`: Type-safe config loader
- `validation_errors`: Missing/invalid config

**Implementation Template**:
```typescript
// File: app/config/env.ts
// [Skill]: Environment Configuration

import { z } from 'zod'

const envSchema = z.object({
  // Next.js specific
  NODE_ENV: z.enum(['development', 'test', 'production']),

  // API endpoints
  NEXT_PUBLIC_API_URL: z.string().url(),

  // Database (backend)
  DATABASE_URL: z.string().optional(),

  // Secrets (server-side only)
  API_SECRET_KEY: z.string().min(32).optional(),

  // Feature flags
  NEXT_PUBLIC_ENABLE_ANALYTICS: z
    .string()
    .transform(v => v === 'true')
    .default('false'),
})

type Env = z.infer<typeof envSchema>

function validateEnv(): Env {
  try {
    return envSchema.parse(process.env)
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('❌ Invalid environment variables:')
      error.errors.forEach(err => {
        console.error(`  ${err.path.join('.')}: ${err.message}`)
      })
    }
    throw new Error('Environment validation failed')
  }
}

export const env = validateEnv()

// Usage in code:
// import { env } from '@/config/env'
// const apiUrl = env.NEXT_PUBLIC_API_URL
```

**Python Backend Config**:
```python
# File: app/config.py
# [Skill]: Environment Configuration (Backend)

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database
    database_url: str = "postgresql://localhost/todo_db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Environment
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Usage:
# from app.config import get_settings
# settings = get_settings()
# DATABASE_URL = settings.database_url
```

**.env.example**:
```bash
# Next.js Frontend
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend API
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
API_SECRET_KEY=your-secret-key-min-32-chars-long
API_HOST=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

**Quality Standards**:
- Type-safe environment validation
- Separate public/private env vars
- .env.example provided
- Validation on startup
- Clear error messages for missing vars

---

### 8. Integration Testing Skill

**Purpose**: Test frontend-backend integration with Playwright/Cypress

**Inputs**:
- `test_scenario`: User flow to test
- `fixtures`: Test data fixtures
- `assertions`: Expected outcomes

**Outputs**:
- `test_file`: E2E test script
- `test_report`: Pass/fail results
- `screenshots`: Visual regression artifacts

**Implementation Template**:
```typescript
// File: tests/e2e/tasks.spec.ts
// [Skill]: Integration Testing

import { test, expect } from '@playwright/test'

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3000')

    // Wait for hydration
    await page.waitForLoadState('networkidle')
  })

  test('should create a new task', async ({ page }) => {
    // Fill form
    await page.fill('input[name="title"]', 'Buy groceries')
    await page.fill('textarea[name="description"]', 'Milk, eggs, bread')

    // Submit
    await page.click('button[type="submit"]')

    // Wait for API response
    await page.waitForResponse(
      response =>
        response.url().includes('/api/tasks') &&
        response.status() === 201
    )

    // Verify task appears in list
    await expect(page.locator('text=Buy groceries')).toBeVisible()
  })

  test('should validate required fields', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"]')

    // Should show validation error
    await expect(
      page.locator('text=Title is required')
    ).toBeVisible()
  })

  test('should mark task as complete', async ({ page }) => {
    // Create a task first
    await page.fill('input[name="title"]', 'Test task')
    await page.click('button[type="submit"]')
    await page.waitForSelector('text=Test task')

    // Mark as complete
    const checkbox = page.locator('input[type="checkbox"]').first()
    await checkbox.check()

    // Wait for API call
    await page.waitForResponse(
      response =>
        response.url().includes('/api/tasks') &&
        response.request().method() === 'PUT'
    )

    // Verify UI update
    await expect(checkbox).toBeChecked()
  })

  test('should delete a task', async ({ page }) => {
    // Create task
    await page.fill('input[name="title"]', 'Task to delete')
    await page.click('button[type="submit"]')
    await page.waitForSelector('text=Task to delete')

    // Delete task
    await page.click('button[aria-label="Delete task"]')

    // Confirm deletion
    await page.click('button:has-text("Confirm")')

    // Verify task removed
    await expect(
      page.locator('text=Task to delete')
    ).not.toBeVisible()
  })
})
```

**Backend Integration Tests**:
```python
# File: tests/integration/test_api.py
# [Skill]: API Integration Testing

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_task():
    """Test task creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "description": "Test description"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
        assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_tasks():
    """Test task listing endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create tasks
        await client.post("/api/tasks", json={"title": "Task 1"})
        await client.post("/api/tasks", json={"title": "Task 2"})

        # List tasks
        response = await client.get("/api/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


@pytest.mark.asyncio
async def test_validation_error():
    """Test validation error handling."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tasks",
            json={"title": ""}  # Empty title
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
```

**Quality Standards**:
- Tests cover happy path and error cases
- Proper test isolation (cleanup between tests)
- Async operations handled correctly
- Assertions verify both UI and API state
- Screenshots captured on failure

---

### 9. Monorepo Setup Skill

**Purpose**: Configure monorepo structure for Next.js + FastAPI full-stack application

**Inputs**:
- `project_name`: Root project name
- `frontend_framework`: "nextjs" | "react" | "vue"
- `backend_framework`: "fastapi" | "flask" | "django"
- `database`: "postgresql" | "mysql" | "sqlite"
- `package_manager`: "npm" | "pnpm" | "yarn"

**Outputs**:
- `monorepo_structure`: Complete directory tree
- `config_files`: Package.json, pyproject.toml, docker-compose.yml
- `claude_md_files`: CLAUDE.md for each service
- `env_templates`: .env.example files for all services

**Implementation Template**:

**Directory Structure**:
```
project-root/
├── .claude/
│   ├── agents/
│   │   ├── nextjs-frontend-developer.md
│   │   ├── fastapi-backend-developer.md
│   │   ├── database-architect.md
│   │   └── auth-security-guardian.md
│   ├── commands/
│   │   ├── sp.adr.md
│   │   ├── sp.plan.md
│   │   ├── sp.specify.md
│   │   └── sp.tasks.md
│   ├── skills/
│   │   └── skills.md
│   └── SKILLS_SYSTEM.md
├── .specify/
│   ├── memory/
│   │   └── constitution.md
│   ├── templates/
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   └── tasks-template.md
│   └── scripts/
├── apps/
│   ├── frontend/                    # Next.js Application
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── tasks/
│   │   │   │       └── route.ts
│   │   │   ├── components/
│   │   │   │   ├── TaskList.tsx
│   │   │   │   ├── TaskForm.tsx
│   │   │   │   └── TaskItem.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useTasks.ts
│   │   │   ├── types/
│   │   │   │   └── task.ts
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── public/
│   │   ├── tests/
│   │   │   └── e2e/
│   │   │       └── tasks.spec.ts
│   │   ├── .env.example
│   │   ├── .env.local
│   │   ├── CLAUDE.md
│   │   ├── next.config.js
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── tailwind.config.ts
│   └── backend/                     # FastAPI Application
│       ├── app/
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   │   └── tasks.py
│       │   │   └── deps.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── database.py
│       │   │   └── security.py
│       │   ├── models/
│       │   │   └── task.py
│       │   ├── services/
│       │   │   └── task_service.py
│       │   ├── schemas/
│       │   │   └── task.py
│       │   └── main.py
│       ├── alembic/
│       │   ├── versions/
│       │   └── env.py
│       ├── tests/
│       │   ├── integration/
│       │   └── unit/
│       ├── .env.example
│       ├── .env
│       ├── CLAUDE.md
│       ├── pyproject.toml
│       ├── poetry.lock
│       └── alembic.ini
├── packages/                        # Shared packages (optional)
│   └── shared-types/
│       ├── src/
│       │   └── task.ts
│       ├── package.json
│       └── tsconfig.json
├── specs/
│   └── phase-1-todo-app/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── history/
│   ├── prompts/
│   └── adr/
├── .env.example
├── .gitignore
├── CLAUDE.md                        # Root project CLAUDE.md
├── docker-compose.yml
├── package.json                     # Workspace root
└── README.md
```

**Root CLAUDE.md**:
```markdown
# Project: Todo Application - Phase II

## Overview
Full-stack todo application with Next.js frontend and FastAPI backend.

## Architecture
- **Frontend**: Next.js 14+ (App Router, TypeScript, Tailwind CSS)
- **Backend**: FastAPI (Python 3.11+, SQLModel, PostgreSQL)
- **Monorepo**: npm/pnpm workspaces

## Project Structure
- `apps/frontend/` - Next.js web application
- `apps/backend/` - FastAPI REST API
- `packages/` - Shared TypeScript types
- `specs/` - Feature specifications
- `.claude/` - AI agent configurations

## Development Commands

### Start All Services
\`\`\`bash
docker-compose up
\`\`\`

### Frontend Development
\`\`\`bash
cd apps/frontend
npm run dev        # Start dev server (http://localhost:3000)
npm run build      # Production build
npm run test       # Run tests
\`\`\`

### Backend Development
\`\`\`bash
cd apps/backend
poetry install
poetry run uvicorn app.main:app --reload  # Start API (http://localhost:8000)
poetry run pytest  # Run tests
\`\`\`

## Environment Setup
1. Copy `.env.example` to `.env` in root
2. Copy `apps/frontend/.env.example` to `apps/frontend/.env.local`
3. Copy `apps/backend/.env.example` to `apps/backend/.env`
4. Update database credentials and API URLs

## Database Setup
\`\`\`bash
cd apps/backend
poetry run alembic upgrade head
\`\`\`

## Agent Guidelines
See `.claude/agents/` for specialized agent configurations:
- `nextjs-frontend-developer.md` - Frontend implementation
- `fastapi-backend-developer.md` - Backend API development
- `database-architect.md` - Database schema and migrations
- `auth-security-guardian.md` - Security and authentication

## Quality Standards
- TypeScript strict mode enabled
- Test coverage > 80%
- All API endpoints documented (OpenAPI)
- WCAG 2.1 AA accessibility compliance
- No `any` types in TypeScript

## Phase II Goals
- ✅ Web-based UI (Next.js)
- ✅ RESTful API (FastAPI)
- ✅ PostgreSQL persistence
- ✅ Docker containerization
- ✅ E2E testing (Playwright)
```

**Frontend CLAUDE.md** (`apps/frontend/CLAUDE.md`):
```markdown
# Frontend: Next.js Todo Application

## Technology Stack
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State**: SWR for data fetching
- **Forms**: React Hook Form + Zod
- **Testing**: Playwright (E2E), Jest (unit)

## Directory Structure
- `app/` - Next.js App Router pages and layouts
- `app/api/` - API route handlers (BFF pattern)
- `app/components/` - React components
- `app/hooks/` - Custom React hooks
- `app/types/` - TypeScript type definitions
- `tests/e2e/` - Playwright tests

## Development
\`\`\`bash
npm install
npm run dev         # http://localhost:3000
npm run build
npm run test
npm run test:e2e
\`\`\`

## Environment Variables
Create `.env.local`:
\`\`\`
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
\`\`\`

## Component Standards
- All components use TypeScript with explicit prop types
- Client components marked with 'use client'
- Server components by default
- Accessible markup (ARIA, semantic HTML)
- Tailwind CSS for styling

## API Integration
- Use SWR for data fetching
- API routes in `app/api/` act as BFF (Backend for Frontend)
- All requests to FastAPI backend go through Next.js API routes
- Zod validation for all request/response data

## Testing
- Unit tests: `*.test.tsx` files
- E2E tests: `tests/e2e/*.spec.ts`
- Run before commits: `npm run test && npm run test:e2e`
```

**Backend CLAUDE.md** (`apps/backend/CLAUDE.md`):
```markdown
# Backend: FastAPI Todo API

## Technology Stack
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ORM**: SQLModel
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Testing**: Pytest
- **Validation**: Pydantic v2

## Directory Structure
- `app/api/routes/` - API endpoint definitions
- `app/models/` - SQLModel database models
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - Business logic layer
- `app/core/` - Configuration, database, security
- `tests/` - Test suites

## Development
\`\`\`bash
poetry install
poetry run uvicorn app.main:app --reload  # http://localhost:8000
poetry run pytest
poetry run alembic upgrade head
\`\`\`

## Environment Variables
Create `.env`:
\`\`\`
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=["http://localhost:3000"]
\`\`\`

## API Design Principles
- RESTful conventions
- Pydantic models for all I/O
- Async/await for database operations
- Proper HTTP status codes
- OpenAPI auto-documentation at /docs

## Database
- SQLModel for ORM
- Alembic for migrations
- PostgreSQL for production
- Proper indexes on frequently queried fields

## Testing
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Run: `poetry run pytest --cov=app`
- Minimum coverage: 80%

## Error Handling
- HTTPException for all errors
- Proper status codes (400, 404, 500)
- Detailed error messages in responses
```

**docker-compose.yml**:
```yaml
# [Skill]: Monorepo Setup - Docker Compose

version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: todo-postgres
    environment:
      POSTGRES_USER: todo_user
      POSTGRES_PASSWORD: todo_password
      POSTGRES_DB: todo_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-PIPE", "pg_isready -U todo_user -d todo_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
    container_name: todo-backend
    environment:
      DATABASE_URL: postgresql://todo_user:todo_password@postgres:5432/todo_db
      API_HOST: 0.0.0.0
      API_PORT: 8000
      CORS_ORIGINS: '["http://localhost:3000"]'
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./apps/backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Next.js Frontend
  frontend:
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile
    container_name: todo-frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NODE_ENV: development
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./apps/frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  postgres_data:

networks:
  default:
    name: todo-network
```

**Root package.json** (Workspace):
```json
{
  "name": "todo-monorepo",
  "version": "2.0.0",
  "private": true,
  "workspaces": [
    "apps/frontend",
    "packages/*"
  ],
  "scripts": {
    "dev": "concurrently \"npm run dev:frontend\" \"npm run dev:backend\"",
    "dev:frontend": "cd apps/frontend && npm run dev",
    "dev:backend": "cd apps/backend && poetry run uvicorn app.main:app --reload",
    "build": "npm run build:frontend",
    "build:frontend": "cd apps/frontend && npm run build",
    "test": "npm run test:frontend && npm run test:backend",
    "test:frontend": "cd apps/frontend && npm run test",
    "test:backend": "cd apps/backend && poetry run pytest",
    "docker:up": "docker-compose up -d",
    "docker:down": "docker-compose down",
    "docker:logs": "docker-compose logs -f"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
```

**Root .env.example**:
```bash
# Project-wide configuration

# Database
POSTGRES_USER=todo_user
POSTGRES_PASSWORD=todo_password
POSTGRES_DB=todo_db
DATABASE_URL=postgresql://todo_user:todo_password@localhost:5432/todo_db

# Backend API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-must-be-at-least-32-characters-long

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# Environment
NODE_ENV=development
ENVIRONMENT=development
```

**Frontend .env.example** (`apps/frontend/.env.example`):
```bash
# Next.js Environment Variables

# Public variables (exposed to browser)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Server-only variables
NODE_ENV=development
```

**Backend .env.example** (`apps/backend/.env.example`):
```bash
# FastAPI Environment Variables

# Database
DATABASE_URL=postgresql://todo_user:todo_password@localhost:5432/todo_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-must-be-at-least-32-characters-long

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Environment
ENVIRONMENT=development
DEBUG=true
```

**Setup Script** (`scripts/setup-monorepo.sh`):
```bash
#!/bin/bash
# [Skill]: Monorepo Setup Script

set -e

echo "🚀 Setting up Todo Monorepo..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p .claude/{agents,commands,skills,system-prompts}
mkdir -p .specify/{memory,templates,scripts}
mkdir -p apps/{frontend,backend}
mkdir -p packages/shared-types/src
mkdir -p specs/phase-2-fullstack
mkdir -p history/{prompts,adr}

# Generate CLAUDE.md files
echo "📝 Generating CLAUDE.md files..."
# (Content generation happens here)

# Setup frontend
echo "⚛️  Setting up Next.js frontend..."
cd apps/frontend
npm init -y
npm install next@latest react@latest react-dom@latest
npm install -D typescript @types/react @types/node
npm install tailwindcss postcss autoprefixer
npm install swr react-hook-form zod @hookform/resolvers
npx tailwindcss init -p
cd ../..

# Setup backend
echo "🐍 Setting up FastAPI backend..."
cd apps/backend
poetry init -n
poetry add fastapi uvicorn sqlmodel alembic psycopg2-binary pydantic-settings
poetry add -D pytest pytest-asyncio httpx
cd ../..

# Copy environment files
echo "🔐 Setting up environment files..."
cp .env.example .env
cp apps/frontend/.env.example apps/frontend/.env.local
cp apps/backend/.env.example apps/backend/.env

# Initialize git
if [ ! -d .git ]; then
  echo "🔧 Initializing git repository..."
  git init
  git add .
  git commit -m "Initial monorepo setup for Phase II"
fi

echo "✅ Monorepo setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env files with your configuration"
echo "2. Run 'docker-compose up' to start all services"
echo "3. Access frontend at http://localhost:3000"
echo "4. Access backend API docs at http://localhost:8000/docs"
```

**Quality Standards**:
- Clear separation between frontend and backend
- Each service has its own CLAUDE.md with specific guidelines
- Docker Compose for local development
- Workspace-based monorepo (npm/pnpm workspaces)
- Environment variables properly scoped
- Consistent naming conventions across services
- Health checks for database readiness
- Volume mounts for hot reloading in development

**Usage**:
```bash
# Setup monorepo
./scripts/setup-monorepo.sh

# Start all services
docker-compose up

# Or use npm scripts
npm run docker:up

# Development (without Docker)
npm run dev
```

---

### 10. API Testing Skill

**Purpose**: Comprehensive REST API testing with authentication, error handling, and integration tools

**Inputs**:
- `api_endpoints`: List of endpoints to test
- `auth_type`: "jwt" | "oauth" | "basic" | "none"
- `test_scenarios`: Happy path, error cases, edge cases
- `testing_tools`: "pytest" | "postman" | "thunder-client" | "httpx"

**Outputs**:
- `test_suite`: Automated test scripts
- `postman_collection`: Postman/Thunder Client collection
- `test_report`: Test results with coverage
- `error_scenarios`: Validated error responses

**Implementation Template**:

**Pytest API Tests** (`tests/integration/test_api_tasks.py`):
```python
# File: tests/integration/test_api_tasks.py
# [Skill]: API Testing

"""
API integration tests for Task endpoints.

Tests REST API endpoints, authentication, and error handling.
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.core.security import create_access_token

# Test fixtures
@pytest.fixture
async def client():
    """HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Authentication headers with JWT token."""
    token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers."""
    return {"Authorization": "Bearer invalid-token-12345"}


# Happy Path Tests
@pytest.mark.asyncio
class TestTasksHappyPath:
    """Test successful API operations."""

    async def test_create_task_success(self, client, auth_headers):
        """Should create task with valid input."""
        response = await client.post(
            "/api/tasks",
            json={
                "title": "Test Task",
                "description": "Test Description"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test Description"
        assert data["id"] is not None
        assert data["completed"] is False
        assert "created_at" in data

    async def test_list_tasks_success(self, client, auth_headers):
        """Should list all tasks."""
        # Create some tasks first
        await client.post(
            "/api/tasks",
            json={"title": "Task 1"},
            headers=auth_headers
        )
        await client.post(
            "/api/tasks",
            json={"title": "Task 2"},
            headers=auth_headers
        )

        # List tasks
        response = await client.get("/api/tasks", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_task_by_id_success(self, client, auth_headers):
        """Should retrieve specific task by ID."""
        # Create task
        create_response = await client.post(
            "/api/tasks",
            json={"title": "Specific Task"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # Get task
        response = await client.get(
            f"/api/tasks/{task_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Specific Task"

    async def test_update_task_success(self, client, auth_headers):
        """Should update existing task."""
        # Create task
        create_response = await client.post(
            "/api/tasks",
            json={"title": "Original Title"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # Update task
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={
                "title": "Updated Title",
                "description": "Updated Description"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated Description"

    async def test_delete_task_success(self, client, auth_headers):
        """Should delete task."""
        # Create task
        create_response = await client.post(
            "/api/tasks",
            json={"title": "Task to Delete"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # Delete task
        response = await client.delete(
            f"/api/tasks/{task_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/tasks/{task_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_mark_task_complete(self, client, auth_headers):
        """Should mark task as completed."""
        # Create task
        create_response = await client.post(
            "/api/tasks",
            json={"title": "Task to Complete"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # Mark complete
        response = await client.patch(
            f"/api/tasks/{task_id}/complete",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True


# Authentication Tests
@pytest.mark.asyncio
class TestAuthentication:
    """Test JWT authentication and authorization."""

    async def test_missing_auth_header(self, client):
        """Should reject request without auth header."""
        response = await client.get("/api/tasks")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "authentication" in data["detail"].lower()

    async def test_invalid_token(self, client, invalid_auth_headers):
        """Should reject invalid JWT token."""
        response = await client.get(
            "/api/tasks",
            headers=invalid_auth_headers
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_expired_token(self, client):
        """Should reject expired JWT token."""
        # Create expired token (expired 1 hour ago)
        from datetime import datetime, timedelta
        expired_token = create_access_token(
            {"sub": "test@example.com"},
            expires_delta=timedelta(hours=-1)
        )

        response = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()

    async def test_malformed_auth_header(self, client):
        """Should reject malformed authorization header."""
        response = await client.get(
            "/api/tasks",
            headers={"Authorization": "InvalidFormat token123"}
        )

        assert response.status_code == 401


# Error Scenario Tests
@pytest.mark.asyncio
class TestErrorScenarios:
    """Test error handling and validation."""

    async def test_create_task_empty_title(self, client, auth_headers):
        """Should reject empty title."""
        response = await client.post(
            "/api/tasks",
            json={"title": ""},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "title" in str(data["detail"]).lower()

    async def test_create_task_title_too_long(self, client, auth_headers):
        """Should reject title exceeding max length."""
        response = await client.post(
            "/api/tasks",
            json={"title": "x" * 201},  # Max is 200
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_create_task_missing_title(self, client, auth_headers):
        """Should reject request without title field."""
        response = await client.post(
            "/api/tasks",
            json={"description": "No title provided"},
            headers=auth_headers
        )

        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data

    async def test_get_nonexistent_task(self, client, auth_headers):
        """Should return 404 for non-existent task."""
        response = await client.get(
            "/api/tasks/99999",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    async def test_update_nonexistent_task(self, client, auth_headers):
        """Should return 404 when updating non-existent task."""
        response = await client.put(
            "/api/tasks/99999",
            json={"title": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_nonexistent_task(self, client, auth_headers):
        """Should return 404 when deleting non-existent task."""
        response = await client.delete(
            "/api/tasks/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_invalid_json_payload(self, client, auth_headers):
        """Should reject invalid JSON."""
        response = await client.post(
            "/api/tasks",
            content="invalid-json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        assert response.status_code == 422

    async def test_sql_injection_attempt(self, client, auth_headers):
        """Should safely handle SQL injection attempts."""
        response = await client.post(
            "/api/tasks",
            json={"title": "'; DROP TABLE tasks; --"},
            headers=auth_headers
        )

        # Should either succeed (sanitized) or fail gracefully
        assert response.status_code in [201, 400]

        # Verify table still exists
        list_response = await client.get("/api/tasks", headers=auth_headers)
        assert list_response.status_code == 200

    async def test_xss_attempt(self, client, auth_headers):
        """Should handle XSS attempts in input."""
        xss_payload = "<script>alert('xss')</script>"
        response = await client.post(
            "/api/tasks",
            json={"title": xss_payload},
            headers=auth_headers
        )

        # Should create task but sanitize output
        if response.status_code == 201:
            data = response.json()
            # Title should be escaped or rejected
            assert "<script>" not in data["title"]


# Edge Case Tests
@pytest.mark.asyncio
class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    async def test_create_task_max_length_title(self, client, auth_headers):
        """Should accept title at max length."""
        response = await client.post(
            "/api/tasks",
            json={"title": "x" * 200},  # Exactly 200 chars
            headers=auth_headers
        )

        assert response.status_code == 201

    async def test_create_task_unicode_characters(self, client, auth_headers):
        """Should handle unicode characters."""
        response = await client.post(
            "/api/tasks",
            json={"title": "Task 任务 📝 Aufgabe"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "任务" in data["title"]
        assert "📝" in data["title"]

    async def test_list_tasks_with_filters(self, client, auth_headers):
        """Should filter tasks by completion status."""
        # Create completed and incomplete tasks
        await client.post(
            "/api/tasks",
            json={"title": "Incomplete"},
            headers=auth_headers
        )

        complete_response = await client.post(
            "/api/tasks",
            json={"title": "Complete"},
            headers=auth_headers
        )
        task_id = complete_response.json()["id"]
        await client.patch(
            f"/api/tasks/{task_id}/complete",
            headers=auth_headers
        )

        # Filter by completed
        response = await client.get(
            "/api/tasks?completed=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(task["completed"] for task in data)

    async def test_concurrent_updates(self, client, auth_headers):
        """Should handle concurrent updates gracefully."""
        # Create task
        create_response = await client.post(
            "/api/tasks",
            json={"title": "Original"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # Simulate concurrent updates
        import asyncio
        responses = await asyncio.gather(
            client.put(
                f"/api/tasks/{task_id}",
                json={"title": "Update 1"},
                headers=auth_headers
            ),
            client.put(
                f"/api/tasks/{task_id}",
                json={"title": "Update 2"},
                headers=auth_headers
            )
        )

        # Both should succeed (last write wins)
        assert all(r.status_code == 200 for r in responses)


# Performance Tests
@pytest.mark.asyncio
class TestPerformance:
    """Test API performance and rate limiting."""

    async def test_list_tasks_pagination(self, client, auth_headers):
        """Should handle pagination for large datasets."""
        # Create 50 tasks
        for i in range(50):
            await client.post(
                "/api/tasks",
                json={"title": f"Task {i}"},
                headers=auth_headers
            )

        # Test pagination
        response = await client.get(
            "/api/tasks?limit=10&offset=0",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    async def test_response_time(self, client, auth_headers):
        """Should respond within acceptable time."""
        import time

        start = time.time()
        response = await client.get("/api/tasks", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should respond within 1 second
```

**Postman Collection** (`tests/postman/todo-api.postman_collection.json`):
```json
{
  "info": {
    "name": "Todo API - Phase II",
    "description": "Comprehensive API testing collection for Todo application",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{jwt_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "type": "string"
    },
    {
      "key": "jwt_token",
      "value": "",
      "type": "string"
    },
    {
      "key": "task_id",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Login",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Response has access token', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.access_token).to.exist;",
                  "    pm.collectionVariables.set('jwt_token', jsonData.access_token);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"testpassword123\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/auth/login",
              "host": ["{{base_url}}"],
              "path": ["api", "auth", "login"]
            }
          }
        }
      ]
    },
    {
      "name": "Tasks - Happy Path",
      "item": [
        {
          "name": "Create Task",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 201', function () {",
                  "    pm.response.to.have.status(201);",
                  "});",
                  "",
                  "pm.test('Task created with ID', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.id).to.exist;",
                  "    pm.collectionVariables.set('task_id', jsonData.id);",
                  "    pm.expect(jsonData.title).to.eql('Test Task');",
                  "    pm.expect(jsonData.completed).to.be.false;",
                  "});",
                  "",
                  "pm.test('Response time under 500ms', function () {",
                  "    pm.expect(pm.response.responseTime).to.be.below(500);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"title\": \"Test Task\",\n  \"description\": \"This is a test task\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/tasks",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks"]
            }
          }
        },
        {
          "name": "List Tasks",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Returns array of tasks', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData).to.be.an('array');",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/tasks",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks"]
            }
          }
        },
        {
          "name": "Get Task by ID",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Task has correct structure', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData).to.have.property('id');",
                  "    pm.expect(jsonData).to.have.property('title');",
                  "    pm.expect(jsonData).to.have.property('completed');",
                  "    pm.expect(jsonData).to.have.property('created_at');",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/tasks/{{task_id}}",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks", "{{task_id}}"]
            }
          }
        },
        {
          "name": "Update Task",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Task updated successfully', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.title).to.eql('Updated Task');",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "PUT",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"title\": \"Updated Task\",\n  \"description\": \"Updated description\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/tasks/{{task_id}}",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks", "{{task_id}}"]
            }
          }
        },
        {
          "name": "Mark Task Complete",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', function () {",
                  "    pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Task marked as completed', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.completed).to.be.true;",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "PATCH",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/tasks/{{task_id}}/complete",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks", "{{task_id}}", "complete"]
            }
          }
        },
        {
          "name": "Delete Task",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 204', function () {",
                  "    pm.response.to.have.status(204);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "DELETE",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/tasks/{{task_id}}",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks", "{{task_id}}"]
            }
          }
        }
      ]
    },
    {
      "name": "Error Scenarios",
      "item": [
        {
          "name": "Create Task - Empty Title",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 400', function () {",
                  "    pm.response.to.have.status(400);",
                  "});",
                  "",
                  "pm.test('Error message present', function () {",
                  "    var jsonData = pm.response.json();",
                  "    pm.expect(jsonData.detail).to.exist;",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"title\": \"\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/tasks",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks"]
            }
          }
        },
        {
          "name": "Get Task - Not Found",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 404', function () {",
                  "    pm.response.to.have.status(404);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/tasks/99999",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks", "99999"]
            }
          }
        },
        {
          "name": "Unauthorized Access",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 401', function () {",
                  "    pm.response.to.have.status(401);",
                  "});"
                ]
              }
            }
          ],
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/tasks",
              "host": ["{{base_url}}"],
              "path": ["api", "tasks"]
            }
          }
        }
      ]
    }
  ]
}
```

**Thunder Client Collection** (`.thunder-client/todo-api.json`):
```json
{
  "clientName": "Thunder Client",
  "collectionName": "Todo API Tests",
  "collectionId": "todo-api-tests",
  "dateExported": "2024-01-07",
  "version": "1.2",
  "folders": [
    {
      "id": "auth-folder",
      "name": "Authentication",
      "requests": []
    },
    {
      "id": "tasks-folder",
      "name": "Task Operations",
      "requests": []
    }
  ],
  "requests": [
    {
      "id": "login-request",
      "name": "Login",
      "url": "{{baseUrl}}/api/auth/login",
      "method": "POST",
      "headers": [],
      "body": {
        "type": "json",
        "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"testpassword123\"\n}",
        "form": []
      },
      "tests": [
        {
          "type": "res-code",
          "value": "200"
        },
        {
          "type": "json-query",
          "value": "json.access_token",
          "action": "istype",
          "expected": "string"
        }
      ]
    }
  ]
}
```

**Test Runner Script** (`scripts/run-api-tests.sh`):
```bash
#!/bin/bash
# [Skill]: API Testing - Test Runner

echo "🧪 Running API Tests..."

# Start services
echo "🚀 Starting services..."
docker-compose up -d
sleep 5

# Wait for API to be ready
echo "⏳ Waiting for API..."
until curl -f http://localhost:8000/health; do
  sleep 2
done

# Run pytest
echo "🐍 Running pytest tests..."
cd apps/backend
poetry run pytest tests/integration/ -v --cov=app --cov-report=html
TEST_EXIT_CODE=$?

# Generate test report
echo "📊 Generating test report..."
poetry run pytest tests/integration/ --html=test-report.html --self-contained-html

# Run Postman collection (if newman installed)
if command -v newman &> /dev/null; then
  echo "📬 Running Postman tests..."
  newman run tests/postman/todo-api.postman_collection.json \
    --environment tests/postman/local.postman_environment.json \
    --reporters cli,html \
    --reporter-html-export postman-report.html
fi

# Cleanup
echo "🧹 Cleaning up..."
docker-compose down

exit $TEST_EXIT_CODE
```

**Quality Standards**:
- All HTTP methods tested (GET, POST, PUT, PATCH, DELETE)
- Authentication tested (valid, invalid, expired tokens)
- Error scenarios covered (400, 401, 404, 422, 500)
- Edge cases validated (unicode, max length, SQL injection)
- Performance benchmarks (response time < 1s)
- Test coverage > 80%
- Postman/Thunder Client collections for manual testing
- Automated CI/CD integration

**Usage**:
```bash
# Run all API tests
./scripts/run-api-tests.sh

# Run specific test class
poetry run pytest tests/integration/test_api_tasks.py::TestAuthentication -v

# Run with coverage
poetry run pytest tests/integration/ --cov=app --cov-report=html

# Import Postman collection
# File -> Import -> tests/postman/todo-api.postman_collection.json
```

---

### 11. Deployment Skill

**Purpose**: Production deployment for Next.js (Vercel), FastAPI (Railway/Render), and Neon DB

**Inputs**:
- `frontend_platform`: "vercel" | "netlify" | "cloudflare"
- `backend_platform`: "railway" | "render" | "fly-io"
- `database_platform`: "neon" | "supabase" | "planetscale"
- `environment`: "staging" | "production"

**Outputs**:
- `deployment_config`: Platform-specific configuration files
- `environment_setup`: Production environment variables
- `ci_cd_pipeline`: GitHub Actions workflow
- `deployment_urls`: Live application URLs

**Implementation Template**:

**Vercel Configuration** (`vercel.json`):
```json
{
  "version": 2,
  "name": "todo-frontend",
  "buildCommand": "cd apps/frontend && npm run build",
  "devCommand": "cd apps/frontend && npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "outputDirectory": "apps/frontend/.next",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url"
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_API_URL": "@api-url"
    }
  },
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.railway.app/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

**Next.js Config** (`apps/frontend/next.config.js`):
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Production optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Image optimization
  images: {
    domains: ['your-backend.railway.app'],
    formats: ['image/avif', 'image/webp'],
  },

  // Headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
        ],
      },
    ]
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig
```

**Railway Configuration** (`railway.json`):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "poetry install --no-dev && poetry run alembic upgrade head"
  },
  "deploy": {
    "startCommand": "poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Render Configuration** (`render.yaml`):
```yaml
# File: render.yaml
# [Skill]: Deployment - Render Config

services:
  # Backend API
  - type: web
    name: todo-backend
    env: python
    region: oregon
    buildCommand: "poetry install --no-dev && poetry run alembic upgrade head"
    startCommand: "poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: todo-db
          property: connectionString
      - key: API_SECRET_KEY
        generateValue: true
      - key: CORS_ORIGINS
        value: '["https://todo-frontend.vercel.app"]'
      - key: ENVIRONMENT
        value: production
      - key: PYTHON_VERSION
        value: 3.11.0
    autoDeploy: true

databases:
  - name: todo-db
    databaseName: todo_production
    plan: starter
    region: oregon
```

**Neon DB Setup Script** (`scripts/setup-neon-db.sh`):
```bash
#!/bin/bash
# [Skill]: Deployment - Neon DB Setup

set -e

echo "🐘 Setting up Neon PostgreSQL Database..."

# Check if Neon CLI is installed
if ! command -v neonctl &> /dev/null; then
    echo "Installing Neon CLI..."
    npm install -g neonctl
fi

# Login to Neon (interactive)
echo "Please login to Neon..."
neonctl auth

# Create project
echo "Creating Neon project..."
PROJECT_ID=$(neonctl projects create \
  --name "todo-production" \
  --region aws-us-east-1 \
  --output json | jq -r '.id')

echo "Project ID: $PROJECT_ID"

# Create database
echo "Creating database..."
neonctl databases create \
  --project-id "$PROJECT_ID" \
  --name "todo_db"

# Get connection string
echo "Retrieving connection string..."
CONNECTION_STRING=$(neonctl connection-string \
  --project-id "$PROJECT_ID" \
  --database-name "todo_db" \
  --role-name "neondb_owner")

echo ""
echo "✅ Neon Database Setup Complete!"
echo ""
echo "Connection String:"
echo "$CONNECTION_STRING"
echo ""
echo "Add this to your backend deployment environment variables:"
echo "DATABASE_URL=$CONNECTION_STRING"
```

**GitHub Actions Workflow** (`.github/workflows/deploy.yml`):
```yaml
# File: .github/workflows/deploy.yml
# [Skill]: Deployment - CI/CD Pipeline

name: Deploy to Production

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

env:
  NODE_VERSION: '18.x'
  PYTHON_VERSION: '3.11'

jobs:
  # Frontend Tests
  test-frontend:
    name: Test Frontend
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: apps/frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd apps/frontend
          npm ci

      - name: Run tests
        run: |
          cd apps/frontend
          npm run test

      - name: Build
        run: |
          cd apps/frontend
          npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}

  # Backend Tests
  test-backend:
    name: Test Backend
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          cd apps/backend
          poetry install

      - name: Run tests
        run: |
          cd apps/backend
          poetry run pytest tests/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./apps/backend/coverage.xml
          flags: backend

  # Deploy Frontend to Vercel
  deploy-frontend:
    name: Deploy Frontend
    needs: [test-frontend, test-backend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
          working-directory: apps/frontend

  # Deploy Backend to Railway
  deploy-backend:
    name: Deploy Backend
    needs: [test-frontend, test-backend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm i -g @railway/cli

      - name: Deploy to Railway
        run: railway up --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        working-directory: apps/backend

  # Health Check
  health-check:
    name: Health Check
    needs: [deploy-frontend, deploy-backend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Check Frontend
        run: |
          curl -f https://your-app.vercel.app || exit 1

      - name: Check Backend API
        run: |
          curl -f https://your-backend.railway.app/health || exit 1

      - name: Check Database Connection
        run: |
          curl -f https://your-backend.railway.app/health/db || exit 1
```

**Environment Variables Guide** (`docs/DEPLOYMENT.md`):
```markdown
# Deployment Guide

## Prerequisites
1. Vercel account
2. Railway/Render account
3. Neon database account
4. GitHub repository

---

## Frontend Deployment (Vercel)

### Step 1: Install Vercel CLI
\`\`\`bash
npm i -g vercel
\`\`\`

### Step 2: Login to Vercel
\`\`\`bash
vercel login
\`\`\`

### Step 3: Configure Environment Variables

Go to Vercel Dashboard → Settings → Environment Variables:

**Production Variables:**
\`\`\`
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NODE_ENV=production
\`\`\`

### Step 4: Deploy
\`\`\`bash
cd apps/frontend
vercel --prod
\`\`\`

### Step 5: Configure Custom Domain (Optional)
Vercel Dashboard → Settings → Domains → Add Domain

---

## Backend Deployment (Railway)

### Step 1: Install Railway CLI
\`\`\`bash
npm i -g @railway/cli
\`\`\`

### Step 2: Login to Railway
\`\`\`bash
railway login
\`\`\`

### Step 3: Create New Project
\`\`\`bash
railway init
\`\`\`

### Step 4: Add Environment Variables

Railway Dashboard → Variables:

**Production Variables:**
\`\`\`
DATABASE_URL=<neon-connection-string>
API_SECRET_KEY=<generate-32-char-key>
CORS_ORIGINS=["https://your-app.vercel.app"]
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=$PORT
\`\`\`

### Step 5: Deploy
\`\`\`bash
cd apps/backend
railway up
\`\`\`

### Step 6: Run Migrations
\`\`\`bash
railway run poetry run alembic upgrade head
\`\`\`

---

## Database Setup (Neon)

### Step 1: Create Neon Account
Visit: https://neon.tech

### Step 2: Create Project
1. Click "Create Project"
2. Choose region (e.g., US East)
3. Name: "todo-production"

### Step 3: Get Connection String
Dashboard → Connection Details → Connection String

Format:
\`\`\`
postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
\`\`\`

### Step 4: Configure in Railway
Add to Railway environment variables as `DATABASE_URL`

### Step 5: Run Migrations
\`\`\`bash
# Set DATABASE_URL locally
export DATABASE_URL="<neon-connection-string>"

# Run migrations
cd apps/backend
poetry run alembic upgrade head
\`\`\`

---

## Environment Variables Reference

### Frontend (.env.local / Vercel)
| Variable | Description | Example |
|----------|-------------|---------|
| \`NEXT_PUBLIC_API_URL\` | Backend API URL | \`https://api.example.com\` |
| \`NODE_ENV\` | Environment | \`production\` |

### Backend (.env / Railway)
| Variable | Description | Example |
|----------|-------------|---------|
| \`DATABASE_URL\` | Neon PostgreSQL connection | \`postgresql://...\` |
| \`API_SECRET_KEY\` | JWT secret (32+ chars) | \`your-secret-key...\` |
| \`CORS_ORIGINS\` | Allowed origins (JSON array) | \`["https://app.com"]\` |
| \`API_HOST\` | Bind address | \`0.0.0.0\` |
| \`API_PORT\` | Port (Railway provides) | \`$PORT\` |
| \`ENVIRONMENT\` | Environment name | \`production\` |

---

## GitHub Actions Setup

### Step 1: Add Secrets to GitHub

Repository → Settings → Secrets and Variables → Actions

**Required Secrets:**
- \`VERCEL_TOKEN\` - From Vercel account settings
- \`VERCEL_ORG_ID\` - From Vercel project settings
- \`VERCEL_PROJECT_ID\` - From Vercel project settings
- \`RAILWAY_TOKEN\` - From Railway account settings
- \`NEXT_PUBLIC_API_URL\` - Your backend URL

### Step 2: Enable Actions
Repository → Actions → Enable workflows

### Step 3: Deploy
Push to main branch triggers automatic deployment

---

## Health Check Endpoints

Add to \`apps/backend/app/main.py\`:

\`\`\`python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """Database health check."""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
\`\`\`

---

## Troubleshooting

### Frontend Build Fails
- Check NEXT_PUBLIC_API_URL is set
- Verify API is accessible
- Check build logs in Vercel dashboard

### Backend Deployment Fails
- Verify DATABASE_URL format
- Check migrations ran successfully
- Review Railway logs

### Database Connection Issues
- Ensure DATABASE_URL includes \`?sslmode=require\`
- Check Neon database is active
- Verify IP allowlist (Neon allows all by default)

### CORS Errors
- Update CORS_ORIGINS in backend env
- Include https:// protocol
- No trailing slash in URLs

---

## Post-Deployment Checklist

- [ ] Frontend accessible at Vercel URL
- [ ] Backend API responds to /health
- [ ] Database migrations applied
- [ ] Environment variables set correctly
- [ ] CORS configured properly
- [ ] Custom domains configured (if applicable)
- [ ] SSL certificates active
- [ ] Monitoring/logging enabled
- [ ] Backup strategy in place
\`\`\`

**Deployment Script** (`scripts/deploy-all.sh`):
```bash
#!/bin/bash
# [Skill]: Deployment - Complete Deployment Script

set -e

echo "🚀 Deploying Todo Application to Production..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check required tools
echo "🔍 Checking required tools..."
command -v vercel >/dev/null 2>&1 || { echo "Vercel CLI not found. Install: npm i -g vercel"; exit 1; }
command -v railway >/dev/null 2>&1 || { echo "Railway CLI not found. Install: npm i -g @railway/cli"; exit 1; }

# Run tests
echo -e "${BLUE}🧪 Running tests...${NC}"
npm run test
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed. Aborting deployment.${NC}"
    exit 1
fi

# Deploy Database Migrations
echo -e "${BLUE}🐘 Running database migrations...${NC}"
cd apps/backend
railway run poetry run alembic upgrade head
cd ../..

# Deploy Backend
echo -e "${BLUE}🐍 Deploying backend to Railway...${NC}"
cd apps/backend
railway up --service backend
BACKEND_URL=$(railway status --json | jq -r '.service.url')
cd ../..

echo -e "${GREEN}✅ Backend deployed: $BACKEND_URL${NC}"

# Update Frontend Environment
echo -e "${BLUE}⚛️  Updating frontend environment...${NC}"
vercel env rm NEXT_PUBLIC_API_URL production || true
echo "$BACKEND_URL" | vercel env add NEXT_PUBLIC_API_URL production

# Deploy Frontend
echo -e "${BLUE}🌐 Deploying frontend to Vercel...${NC}"
cd apps/frontend
vercel --prod
FRONTEND_URL=$(vercel inspect --json | jq -r '.url')
cd ../..

echo -e "${GREEN}✅ Frontend deployed: $FRONTEND_URL${NC}"

# Health Checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Check Backend
if curl -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    exit 1
fi

# Check Frontend
if curl -f "https://$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend health check passed${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Frontend: https://$FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "API Docs: $BACKEND_URL/docs"
echo ""
echo "Next steps:"
echo "1. Test the application manually"
echo "2. Monitor logs for errors"
echo "3. Set up custom domain (optional)"
```

**Quality Standards**:
- Zero-downtime deployments
- Automated health checks
- Database migrations run before deployment
- Environment variables validated
- SSL/TLS enabled by default
- CORS properly configured
- Error monitoring (Sentry integration ready)
- Automatic rollback on failure

**Usage**:
```bash
# Full automated deployment
./scripts/deploy-all.sh

# Deploy frontend only
cd apps/frontend && vercel --prod

# Deploy backend only
cd apps/backend && railway up

# Run migrations only
railway run poetry run alembic upgrade head

# Check deployment status
vercel inspect
railway status
```

---

## 🔧 Skill Composition Patterns

### Pattern 1: Full-Stack Feature Flow

**Create Task Feature**:
```
1. Form Handling Skill (collect user input)
   ↓
2. API Route Skill (Next.js route handler)
   ↓
3. FastAPI Endpoint Skill (backend API)
   ↓
4. Database Schema Skill (persist to DB)
   ↓
5. Frontend Data Fetching Skill (update UI)
```

### Pattern 2: Data Validation Chain

**Request Validation**:
```
Frontend: Zod schema validation
    ↓
API Route: NextRequest validation
    ↓
Backend: Pydantic model validation
    ↓
Database: SQLModel constraints
```

### Pattern 3: Error Handling Flow

**Error Propagation**:
```
Database Error
    ↓
FastAPI HTTP Exception (with status code)
    ↓
Next.js API Route (transform to client format)
    ↓
Frontend Error Boundary (user-friendly message)
    ↓
Toast/Alert Component (display to user)
```

---

## 📚 Skill Usage by Agent

### Next.js Frontend Developer Agent
- Next.js Component Skill
- API Route Skill
- Frontend Data Fetching Skill
- Form Handling Skill
- Environment Configuration Skill

### FastAPI Backend Developer Agent
- FastAPI Endpoint Skill
- Database Schema Skill
- Environment Configuration Skill (backend)
- Integration Testing Skill (API tests)

### Database Architect Agent
- Database Schema Skill
- Migration generation
- Index optimization
- Query performance analysis

### Auth Security Guardian Agent
- Environment Configuration Skill (secrets)
- CORS configuration
- JWT token validation
- Input sanitization

---

## 🎯 Phase II Skill Requirements

### Must Have
- [x] Next.js 14+ with App Router
- [x] TypeScript strict mode
- [x] FastAPI with Pydantic v2
- [x] SQLModel for ORM
- [x] PostgreSQL database
- [x] RESTful API design
- [x] Proper error handling
- [x] E2E tests (Playwright)

### Quality Gates
- Type safety: 100% (no `any` types)
- Test coverage: >80%
- API documentation: OpenAPI/Swagger
- Accessibility: WCAG 2.1 AA
- Performance: Lighthouse score >90

---

## 📖 Creating Phase II Skills

When creating skills for Phase II:

1. **Build on Phase I**: Reuse Phase I business logic, add web/API layer
2. **Separation of Concerns**: Frontend components ≠ Backend logic
3. **Type Safety**: TypeScript + Pydantic for end-to-end types
4. **Testing**: Unit tests (Jest/Pytest) + Integration tests (Playwright)
5. **Documentation**: TSDoc/docstrings + OpenAPI specs

---

## 🚀 Next Steps (Phase III Preview)

Phase III will add:
- Authentication (NextAuth.js / Better Auth)
- User-specific task isolation
- AI chatbot integration (MCP)
- Real-time updates (WebSockets)

Skills to prepare:
- Auth integration skill
- WebSocket communication skill
- MCP tool invocation skill
- User context management skill

---

This skills document provides the foundation for Phase II agents to transform the console app into a production-ready web application!
