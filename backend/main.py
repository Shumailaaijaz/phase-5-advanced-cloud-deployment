from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from sqlmodel import SQLModel, select # SQLModel zaroori hai tables banane ke liye
from database.session import engine
from core.config import settings

# Routers Import
from api.tasks import router as tasks_router
from api.chat import router as chat_router
try:
    from api.auth import router as auth_router
except ImportError:
    auth_router = None

from middleware import CanonicalPathMiddleware
from api.errors import register_exception_handlers
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Todo API",
    description="Secure FastAPI backend with JWT and Neon PostgreSQL",
    version="1.0.0",
)

# --- 1. DATABASE TABLES CREATION ---
# Ye function backend start hote hi 'user' aur 'task' tables bana dega
@app.on_event("startup")
def on_startup():
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables ready!")

# --- 2. CORS FIX ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CanonicalPathMiddleware)

# --- 3. ROUTERS (Fixed Duplicates) ---
if auth_router:
    # Prefix /api/auth lagane se frontend ki request sahi jagah jayegi
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

app.include_router(tasks_router)
app.include_router(chat_router)  # Chat API endpoints

# Register chat API exception handlers
register_exception_handlers(app)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    codes = {401: "unauthorized", 403: "user_id_mismatch", 404: "not_found"}
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": codes.get(exc.status_code, "unknown_error")}
    )

@app.post("/reminder-cron")
async def reminder_cron(request: Request):
    """Dapr cron binding input route — invoked every minute by reminder-cron binding.
    Delegates to the existing check_reminders logic."""
    from database.session import get_session
    session = next(get_session())
    try:
        from api.tasks import check_reminders as _check_reminders
        result = await _check_reminders(session=session)
        return result
    finally:
        session.close()


# --- WEBSOCKET: Real-time task sync ---
ws_connections: dict[int, list[WebSocket]] = {}
ws_logger = logging.getLogger("websocket")


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Real-time sync: clients connect here to receive live task updates."""
    await websocket.accept()
    if user_id not in ws_connections:
        ws_connections[user_id] = []
    ws_connections[user_id].append(websocket)
    ws_logger.info(f"WebSocket connected: user_id={user_id}")
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        ws_connections[user_id].remove(websocket)
        if not ws_connections[user_id]:
            del ws_connections[user_id]
        ws_logger.info(f"WebSocket disconnected: user_id={user_id}")


async def broadcast_task_event(user_id: int, event_type: str, data: dict):
    """Broadcast a task event to all connected WebSocket clients for a user."""
    if user_id in ws_connections:
        message = json.dumps({"event_type": event_type, "data": data})
        dead = []
        for ws in ws_connections[user_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            ws_connections[user_id].remove(ws)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Todo API"}

@app.get("/health")
@limiter.limit("10/minute")
def health_check(request: Request):
    return {"status": "healthy", "db_connected": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)