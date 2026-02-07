# Demo Assets — Phase V: Advanced Cloud Deployment

Screenshots and demo materials for the Todo AI Chatbot hackathon submission.

## Screenshots

| # | Screenshot | Description |
|---|-----------|-------------|
| 1 | `01-login.png` | Login page with Better Auth email/password |
| 2 | `02-dashboard.png` | Dashboard showing tasks with P1-P4 priorities, tags, due dates |
| 3 | `03-chat.png` | AI chat interface — natural language task management |
| 4 | `04-task-create.png` | Creating a task with priority, tags, recurrence, and reminder |
| 5 | `05-consumer-logs.png` | Recurring task consumer processing task.completed event |
| 6 | `06-helm-template.png` | Helm template rendering all Dapr components + consumers |

## How to Capture Screenshots

```bash
# 1. Start backend
cd backend && ./venv/bin/python -m uvicorn main:app --reload

# 2. Start frontend
cd frontend && npm run dev

# 3. Open http://localhost:3000 in browser
# 4. Log in, create tasks, use chat — screenshot each page
# 5. Save screenshots in this folder as PNG files
```

## Demo Flow (2-minute walkthrough)

1. Open dashboard — show empty task list
2. Use chat: "Add a P1 task called 'Deploy to production' tagged 'devops' with weekly recurrence and 30-min reminder"
3. Show task appears with priority badge, tag chips, recurrence icon
4. Filter by tag: click "devops" → only matching tasks shown
5. Search: type "deploy" → full-text search results
6. Complete the recurring task → show next occurrence auto-created
7. Show consumer logs: `task.completed` event processed, new `task.created` event emitted
8. Show Helm chart: `helm template charts/todo-app --set dapr.enabled=true`
