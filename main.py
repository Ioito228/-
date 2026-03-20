import time
import io
import base64
import qrcode
import hashlib
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- БАЗА ДАННЫХ ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./rostelecom.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    position = Column(String)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

Base.metadata.create_all(bind=engine)

# --- УПРОЩЕННАЯ БЕЗОПАСНОСТЬ (Hashlib) ---
def get_password_hash(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# --- API ЭНДПОИНТЫ ---

@app.post("/api/register")
def register(
    full_name: str = Form(...), 
    position: str = Form(...), 
    username: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Логин уже занят")
    
    new_user = User(
        full_name=full_name, 
        position=position, 
        username=username, 
        hashed_password=get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    return {"status": "ok"}

@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    return {
        "id": user.id,
        "full_name": user.full_name,
        "position": user.position
    }

@app.get("/api/generate_qr/{user_id}")
def generate_qr(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")

    timestamp = int(time.time())
    # Формат данных QR: Имя|ID|Время
    qr_data = f"RTK|{user.full_name}|{user.id}|{timestamp}"
    
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {"qr": img_base64, "expires": 300}

# Монтируем статику (должно быть в конце)
app.mount("/", StaticFiles(directory="static", html=True), name="static")