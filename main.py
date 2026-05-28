# ============================================
# MANTHAN AI — Main Entry Point (Cloud Database Enabled)
# File: main.py
# Run: python main.py
# ============================================

import os, io, zipfile
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel
from core.router import ask_ai
from core.auth import request_otp, verify_otp, verify_token, logout_token, get_active_users
import razorpay

# ── 🗄️ ADVANCED DATABASE LOGIC (SQLAlchemy) ────────────────
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# 🚨 CLOUD DB LINK: Agar .env me DATABASE_URL nahi hai, to local users.db banayega
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")

# Fix for Render/Heroku Postgres URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Check thread safety only for SQLite local database
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    plan = Column(String, default="Free Tier")
    queries = Column(Integer, default=0)
    last_date = Column(String)

# Database Helper Functions
def get_user_state(email: str):
    db = SessionLocal()
    today = datetime.now().strftime("%Y-%m-%d")
    user = db.query(UserDB).filter(UserDB.email == email).first()
    
    if not user:
        new_user = UserDB(email=email, plan="Free Tier", queries=0, last_date=today)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()
        return {"plan": "Free Tier", "queries": 0, "last_date": today}
    
    if user.last_date != today:
        user.queries = 0
        user.last_date = today
        db.commit()
        
    plan, queries, last_date = user.plan, user.queries, user.last_date
    db.close()
    return {"plan": plan, "queries": queries, "last_date": today}

def upgrade_user_plan(email: str, new_plan: str):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.email == email).first()
    today = datetime.now().strftime("%Y-%m-%d")
    if user:
        user.plan = new_plan
    else:
        new_user = UserDB(email=email, plan=new_plan, queries=0, last_date=today)
        db.add(new_user)
    db.commit()
    db.close()

def increment_query(email: str):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if user:
        user.queries += 1
        db.commit()
    db.close()

# ── Lifespan ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Manthan AI v3.0 Starting...")
    Base.metadata.create_all(bind=engine)
    print("🗄️  Database Connected & Synced (Cloud/Local Ready)")
    yield
    print("🛑 Manthan AI Stopped.")

# ── App Setup ─────────────────────────────────
app = FastAPI(title="Manthan AI", version="3.0", lifespan=lifespan)
os.makedirs("temp", exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Pydantic Models ───────────────────────────
class OTPRequest(BaseModel): email: str
class OTPVerify(BaseModel): email: str; otp: str
class LogoutRequest(BaseModel): token: str
class OrderRequest(BaseModel): amount: int; plan_name: str
class VerifyPayment(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    email: str
    plan: str

# ── Auth Helper ───────────────────────────────
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login karo pehle!")
    token = authorization.split(" ")[1]
    result = verify_token(token)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail="Session expire ho gaya! Dobara login karo.")
    return result["email"]

# ══════════════════════════════════════════════
# FRONTEND & AUTH ENDPOINTS
# ══════════════════════════════════════════════
@app.get("/{file_name}", response_class=HTMLResponse)
async def serve_file(file_name: str = "index.html"):
    if file_name not in ["", "login", "dashboard", "chat"]: file_name = "index.html"
    elif file_name == "login": file_name = "login.html"
    elif file_name == "dashboard": file_name = "dashboard.html"
    elif file_name == "chat": file_name = "index.html"
    path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: return f.read()
    return "<h2>File not found!</h2>"

# 🚨 DONO RASTE EK SATH SET KAR DIYE HAIN (FRONTEND COMPATIBILITY)

@app.post("/auth/send-otp")
@app.post("/api/auth/send-otp")
async def send_otp(body: OTPRequest): 
    return request_otp(body.email)

@app.post("/auth/verify-otp")
@app.post("/api/auth/verify-otp")
async def verify_otp_endpoint(body: OTPVerify): 
    return verify_otp(body.email, body.otp)
@app.get("/api/auth/me")
async def get_me(user_email: str = Depends(get_current_user)): 
    state = get_user_state(user_email)
    return {"email": user_email, "logged_in": True, "plan": state["plan"], "queries_used": state["queries"]}

# ══════════════════════════════════════════════
# PAYMENT GATEWAY ENDPOINTS (RAZORPAY)
# ══════════════════════════════════════════════
# 🚨 TUMHARI NAYI KEYS YAHAN ADD KAR DI GAYI HAIN:
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_Suf6Oyc6wfwmJ0")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "FeRwgIdo9TFteLZB1V3InI2L")

try: razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except: razorpay_client = None

@app.post("/api/payment/create-order")
async def create_order(request: OrderRequest):
    if not razorpay_client: return {"error": "Razorpay client not configured properly."}
    try:
        order_amount = request.amount * 100
        razorpay_order = razorpay_client.order.create(dict(
            amount=order_amount, currency="INR", receipt=f"receipt_{request.plan_name.replace(' ', '_').lower()}", payment_capture="1"
        ))
        return {"order_id": razorpay_order["id"], "amount": order_amount, "key": RAZORPAY_KEY_ID}
    except Exception as e: return {"error": str(e)}

@app.post("/api/payment/verify")
async def verify_payment(data: VerifyPayment):
    if not razorpay_client: return {"status": "failed", "message": "Razorpay error"}
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': data.razorpay_order_id,
            'razorpay_payment_id': data.razorpay_payment_id,
            'razorpay_signature': data.razorpay_signature
        })
        upgrade_user_plan(data.email, data.plan)
        print(f"💰 SUCCESS: {data.email} upgraded to {data.plan}")
        return {"status": "success", "message": f"Welcome to {data.plan}, payment successful!"}
    except Exception as e: return {"status": "failed", "message": str(e)}

# ══════════════════════════════════════════════
# CHAT ENDPOINT (Protected & Plan Enforced)
# ══════════════════════════════════════════════
@app.post("/api/chat")
async def chat_endpoint(
    task: str = Form(default="chat"),
    message: str = Form(...),
    file: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    user_state = get_user_state(user_email)
    current_plan = user_state["plan"]
    queries_used = user_state["queries"]

    if "Free" in current_plan and queries_used >= 20:
        return {"response": "❌ **Limit Reached!** You have used your 20 free queries for today. Please click on **💎 Upgrade Plan** to get unlimited access!"}

    file_bytes = None
    mime_type  = None

    if file:
        mime_type  = file.content_type
        filename   = file.filename.lower()

        if mime_type.startswith("image/"):
            if "Free" in current_plan:
                return {"response": "🖼️ **Pro Feature Locked!** Image Vision extraction is only available in the **Pro Developer** plan. Please upgrade to upload images."}
            file_bytes = await file.read()

        elif filename.endswith(".zip"):
            if "Elite" not in current_plan:
                return {"response": "📁 **Elite Feature Locked!** Multi-file ZIP Directory Reads require the **Elite Architecture** plan. Please upgrade to process full repositories."}
            
            file_bytes = await file.read()
            try:
                context = ""
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    for info in z.infolist():
                        if info.is_dir() or "__MACOSX" in info.filename: continue
                        if info.filename.lower().endswith(('.py','.js','.ts','.html','.css','.json','.txt','.cpp','.java','.md')):
                            try: context += f"\n\n--- FILE: {info.filename} ---\n{z.read(info.filename).decode('utf-8', errors='ignore')}"
                            except: continue
                if context: message = f"{message}\n\n[ZIP Context]:{context[:5000]}"
            except Exception as e: message = f"{message}\n\n[ZIP Error: {str(e)}]"
            file_bytes = None
            mime_type  = None

    increment_query(user_email)
    result = await ask_ai(task=task, user_message=message, file_bytes=file_bytes, mime_type=mime_type)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)