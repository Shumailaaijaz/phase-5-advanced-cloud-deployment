# Todo API Backend

This is a secure, production-ready FastAPI backend with Neon PostgreSQL storage and strict multi-user isolation via JWT — implementing all 5 Basic Level Todo features as REST API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database URL and secret key
```

3. Start the development server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
All endpoints require JWT authentication in the Authorization header:
```
Authorization: Bearer <jwt_token_here>
```

### Rate Limiting
The API implements rate limiting to prevent abuse:
- Create Task: 10 requests per minute
- List/Get Tasks: 30 requests per minute
- Update/Delete/Toggle: 10 requests per minute
- Health Check: 10 requests per minute

Exceeding these limits will result in a `429 Too Many Requests` response.

### Logging
All API requests are logged with:
- Client IP address
- Requested endpoint
- User ID
- Success or error status
- Timestamp

### Task Management Endpoints

#### List all tasks for a user
- **Endpoint**: `GET /api/{user_id}/tasks`
- **Authentication**: Required JWT token
- **Path Parameter**: `{user_id}` - authenticated user ID
- **Response**: `200 OK` with array of Task objects

#### Create a new task
- **Endpoint**: `POST /api/{user_id}/tasks`
- **Authentication**: Required JWT token
- **Path Parameter**: `{user_id}` - authenticated user ID
- **Request Body**:
```json
{
  "title": "New task title",
  "description": "Optional task description",
  "completed": false
}
```
- **Response**: `201 Created` with created Task object

#### Get a specific task
- **Endpoint**: `GET /api/{user_id}/tasks/{id}`
- **Authentication**: Required JWT token
- **Path Parameters**: `{user_id}`, `{id}` - task ID
- **Response**: `200 OK` with Task object or `404 Not Found`

#### Update a task
- **Endpoint**: `PUT /api/{user_id}/tasks/{id}`
- **Authentication**: Required JWT token
- **Path Parameters**: `{user_id}`, `{id}` - task ID
- **Request Body**:
```json
{
  "title": "Updated task title",
  "description": "Updated task description",
  "completed": true
}
```
- **Response**: `200 OK` with updated Task object or `404 Not Found`

#### Delete a task
- **Endpoint**: `DELETE /api/{user_id}/tasks/{id}`
- **Authentication**: Required JWT token
- **Path Parameters**: `{user_id}`, `{id}` - task ID
- **Response**: `200 OK` on success or `404 Not Found`

#### Toggle task completion
- **Endpoint**: `PATCH /api/{user_id}/tasks/{id}/complete`
- **Authentication**: Required JWT token
- **Path Parameters**: `{user_id}`, `{id}` - task ID
- **Response**: `200 OK` with updated Task object or `404 Not Found`

## Error Responses

- `401 Unauthorized`: `{"error": "unauthorized"}`
- `403 Forbidden`: `{"error": "user_id_mismatch"}`
- `404 Not Found`: `{"error": "not_found"}`
- `422 Unprocessable Entity`: `{"error": "validation_error"}` (e.g., empty task title)
- `429 Too Many Requests`: Rate limit exceeded

## Security

- All endpoints require JWT authentication
- User isolation: user_id path parameter must match JWT user_id
- No user can access, modify, or delete another user's tasks
- Canonical path validation prevents inconsistent URL formats
- Rate limiting prevents API abuse

## Health Check

- **Endpoint**: `GET /health`
- **Response**: Health status of the API

## OpenAPI Documentation

Interactive API documentation is available at:
- `/docs` - Interactive Swagger UI
- `/redoc` - ReDoc documentation
- `/openapi.json` - Raw OpenAPI specification