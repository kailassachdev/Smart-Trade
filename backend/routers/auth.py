"""
routers/auth.py
---------------
Authentication endpoints: register, login, refresh.

ARCHITECTURAL IMPROVEMENTS:
- #7: JWT now has expiry (ACCESS_TOKEN_EXPIRE_MINUTES)
- #7: /login sets HttpOnly cookie in addition to JSON response body
- #7: /refresh endpoint for rolling sessions
- #8: Structured logging for all auth events
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
import jwt
import os

import models
from database import get_db
from logging_config import get_logger, USER_AUTH

log = get_logger("auth")

router = APIRouter(tags=["auth"])

SECRET_KEY              = os.getenv("SECRET_KEY", "REPLACE_IN_PRODUCTION_WITH_A_STRONG_SECRET_32CHARS+")
ALGORITHM               = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── Shared auth utilities ─────────────────────────────────────────────────────
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    # Bcrypt max is 72 bytes; truncate safely
    if len(password.encode("utf-8")) > 72:
        password = password[:30]
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})          # IMPROVEMENT #7: expiry added
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ── Dependency: resolve current user from token ───────────────────────────────
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ── Models ────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed = get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create empty wallet with default risk settings
    db.add(models.Wallet(user_id=new_user.id, balance=0.0))
    db.commit()

    log.info(USER_AUTH, event="register", username=user.username, user_id=new_user.id)
    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        log.warning(USER_AUTH, event="login_failed", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.username})

    # IMPROVEMENT #7: Set HttpOnly cookie (safer than localStorage)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,           # JS cannot read this cookie
        samesite="strict",       # CSRF protection
        secure=False,            # Set to True in production with HTTPS
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    log.info(USER_AUTH, event="login_success", username=user.username, user_id=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh_token(response: Response, current_user: models.User = Depends(get_current_user)):
    """IMPROVEMENT #7: Rolling session — issue a fresh token before the old one expires."""
    new_token = create_access_token(data={"sub": current_user.username})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="strict",
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    log.info(USER_AUTH, event="token_refresh", username=current_user.username)
    return {"access_token": new_token, "token_type": "bearer"}
