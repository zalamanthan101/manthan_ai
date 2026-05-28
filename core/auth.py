# ============================================
# MANTHAN AI — Email OTP Auth System
# File: core/auth.py
# ============================================

import os, random, string, smtplib, hashlib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# In-memory stores
otp_store   = {}  # { email: { otp, expires_at, attempts } }
token_store = {}  # { token: { email, created_at } }

SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
OTP_EXPIRY    = 300    # 5 minutes
TOKEN_EXPIRY  = 86400  # 24 hours
MAX_ATTEMPTS  = 3      # Max wrong OTP tries


# ── Generate OTP ──────────────────────────────
def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


# ── Generate Token ────────────────────────────
def generate_token(email: str) -> str:
    raw = f"{email}{time.time()}{random.random()}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Send OTP Email ────────────────────────────
def send_otp_email(email: str, otp: str) -> bool:
    # Dev mode — SMTP nahi hai to console me print karo
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"\n{'='*40}")
        print(f"🔑 DEV MODE OTP")
        print(f"   Email : {email}")
        print(f"   OTP   : {otp}")
        print(f"{'='*40}\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔥 Manthan AI OTP: {otp}"
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = email

        html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#05050d;font-family:'Courier New',monospace">
<div style="max-width:480px;margin:40px auto;background:#0e0e1a;border:1px solid #1e1e30;border-radius:16px;overflow:hidden">

  <!-- Header -->
  <div style="background:#00ffa308;border-bottom:1px solid #00ffa320;padding:24px;text-align:center">
    <span style="color:#00ffa3;font-size:22px;font-weight:800;letter-spacing:3px">MANTHAN AI</span>
    <div style="color:#454568;font-size:11px;margin-top:4px;letter-spacing:1px">AI CODING ASSISTANT</div>
  </div>

  <!-- Body -->
  <div style="padding:32px">
    <p style="color:#aaa;font-size:14px;margin-bottom:8px">Hello! 👋</p>
    <p style="color:#e2e2f0;font-size:14px;margin-bottom:28px">
      Your <b style="color:#00ffa3">Manthan AI</b> login OTP:
    </p>

    <!-- OTP Box -->
    <div style="background:#05050d;border:1px solid #1e1e30;border-radius:12px;padding:28px;text-align:center;margin-bottom:28px">
      <div style="font-size:44px;font-weight:800;letter-spacing:14px;color:#00ffa3;font-family:'Courier New',monospace">
        {otp}
      </div>
    </div>

    <!-- Info -->
    <div style="background:#0a0a14;border-radius:8px;padding:14px">
      <p style="color:#454568;font-size:12px;margin-bottom:6px">⏱️ Yeh OTP <b style="color:#ffd60a">5 minutes</b> me expire ho jayega.</p>
      <p style="color:#454568;font-size:12px;margin-bottom:6px">🔒 Kisi ko share mat karna.</p>
      <p style="color:#454568;font-size:12px">❌ Tune request nahi ki to ignore karo.</p>
    </div>
  </div>

  <!-- Footer -->
  <div style="border-top:1px solid #1e1e30;padding:16px;text-align:center">
    <span style="color:#2a2a45;font-size:11px">Manthan AI — AI Coding Assistant 🇮🇳</span>
  </div>
</div>
</body>
</html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())

        print(f"✅ OTP sent to {email}")
        return True

    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False


# ── Request OTP ───────────────────────────────
def request_otp(email: str) -> dict:
    email = email.lower().strip()

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return {"success": False, "message": "Please enter a valid email address!"}

    # Rate limit — 1 min me dobara nahi
    existing = otp_store.get(email)
    if existing:
        time_left = existing["expires_at"] - time.time()
        if time_left > (OTP_EXPIRY - 60):
            wait = int(time_left - (OTP_EXPIRY - 60))
            return {"success": False, "message": f"Please wait {wait} seconds before requesting again!"}

    otp = generate_otp()
    otp_store[email] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY,
        "attempts": 0
    }

    sent = send_otp_email(email, otp)
    if sent:
        return {"success": True, "message": f"OTP sent to {email} pe! Check your inbox/spam. 📧"}
    else:
        del otp_store[email]
        return {"success": False, "message": "Email could not be sent! Check SMTP settings in .env"}


# ── Verify OTP ────────────────────────────────
def verify_otp(email: str, otp: str) -> dict:
    email = email.lower().strip()
    record = otp_store.get(email)

    if not record:
        return {"success": False, "message": "Please request an OTP first!"}

    if time.time() > record["expires_at"]:
        del otp_store[email]
        return {"success": False, "message": "OTP has expired! Please request a new one."}

    # Max attempts check
    if record["attempts"] >= MAX_ATTEMPTS:
        del otp_store[email]
        return {"success": False, "message": f"{MAX_ATTEMPTS} incorrect attempts! Please request a new OTP."}

    if record["otp"] != otp.strip():
        otp_store[email]["attempts"] += 1
        left = MAX_ATTEMPTS - otp_store[email]["attempts"]
        return {"success": False, "message": f"Incorrect OTP! {left} attempts attempts remaining."}

    # OTP sahi — token banao
    del otp_store[email]
    token = generate_token(email)
    token_store[token] = {
        "email": email,
        "created_at": time.time()
    }

    print(f"✅ Login: {email}")
    return {
        "success": True,
        "token": token,
        "email": email,
        "message": "Login successful! 🎉"
    }


# ── Verify Token ──────────────────────────────
def verify_token(token: str) -> dict:
    if not token:
        return {"valid": False, "email": None}

    record = token_store.get(token)
    if not record:
        return {"valid": False, "email": None}

    if time.time() - record["created_at"] > TOKEN_EXPIRY:
        del token_store[token]
        return {"valid": False, "email": None}

    return {"valid": True, "email": record["email"]}


# ── Logout ────────────────────────────────────
def logout_token(token: str) -> dict:
    if token in token_store:
        email = token_store[token].get("email", "")
        del token_store[token]
        print(f"👋 Logout: {email}")
    return {"success": True, "message": "Logged out successfully!"}


# ── Get All Active Users (Admin) ──────────────
def get_active_users() -> list:
    now = time.time()
    return [
        {"email": v["email"], "since": int(now - v["created_at"])}
        for v in token_store.values()
        if now - v["created_at"] < TOKEN_EXPIRY
    ]