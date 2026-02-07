from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlmodel import Session, select
from database.session import get_session
from models.user import User
from core.security import get_password_hash, create_access_token, verify_password
from api.deps import get_current_user
from typing import Optional

router = APIRouter()

@router.post("/sign-up/email")
def signup(user_data: dict = Body(...), session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user_data["email"])
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
        full_name=user_data.get("name", "") # Frontend 'name' bhej raha hai
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User created successfully"}

@router.post("/sign-in/email")
def login(data: dict = Body(...), session: Session = Depends(get_session)):
    statement = select(User).where(User.email == data["email"])
    user = session.exec(statement).first()
    
    if not user or not verify_password(data["password"], user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    # Next.js frontend ko ye structure chahiye redirect ke liye
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.full_name}
    }

@router.get("/get-session")
async def get_auth_session(request: Request, session: Session = Depends(get_session)):
    # Header se token nikalne ki koshish karein
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        # 403 dene ke bajaye null session bhejien
        return {"user": None, "session": None}
    
    try:
        token = auth_header.split(" ")[1]
        user_info = get_current_user(token) 
        return {
            "user": user_info, 
            "session": {"active": True}
        }
    except Exception:
        # Agar token expire hai ya invalid, tab bhi 403 na dein
        return {"user": None, "session": None}