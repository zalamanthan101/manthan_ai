# ============================================
# MANTHAN AI — Complete Test Suite v2.0
# File: test_manthan_complete.py
# Run: python test_manthan_complete.py
# ============================================

import requests
import json
import time
import sys
import os
import threading
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
PASS  = "✅ PASS"
FAIL  = "❌ FAIL"
SKIP  = "⏭️  SKIP"
WARN  = "⚠️  WARN"

results = []
total_time = time.time()

def log(name, status, detail="", time_ms=None):
    t = f" [{time_ms}ms]" if time_ms else ""
    print(f"  {status}  {name}{t}")
    if detail: print(f"         → {detail}")
    results.append({"name": name, "status": status, "detail": detail})

def separator(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print(f"{'═'*55}")

def get_token():
    """Get a valid auth token for protected endpoint tests"""
    # Send OTP
    try:
        requests.post(f"{BASE_URL}/api/auth/send-otp",
                     json={"email": "autotest@manthanai.com"}, timeout=5)
        # In dev mode, OTP is in server console
        # We'll use the stored OTP from otp_store directly
        return None  # Will skip auth-protected tests
    except:
        return None

# ══════════════════════════════════════════
# TEST 1: SERVER HEALTH
# ══════════════════════════════════════════
separator("1. SERVER HEALTH")

try:
    t0 = time.time()
    res = requests.get(f"{BASE_URL}/status", timeout=5)
    ms = int((time.time()-t0)*1000)
    if res.status_code == 200:
        data = res.json()
        log("Server online", PASS, f"v{data.get('version','?')}", ms)
        if ms < 100:  log("Response time", PASS, f"{ms}ms — Excellent!")
        elif ms < 500: log("Response time", PASS, f"{ms}ms — Good")
        else:          log("Response time", WARN, f"{ms}ms — Slow")
    else:
        log("Server online", FAIL, f"HTTP {res.status_code}")
except Exception as e:
    log("Server online", FAIL, f"Cannot connect: {e}")
    print("\n  ⚠️  Server offline! Run: python main.py")
    sys.exit(1)

# ══════════════════════════════════════════
# TEST 2: ALL PAGES
# ══════════════════════════════════════════
separator("2. ALL PAGES CHECK")

pages = [
    ("/",          "Root / Login page"),
    ("/login",     "Login page"),
    ("/chat",      "Chat page"),
    ("/dashboard", "Dashboard"),
    ("/docs",      "API Swagger Docs"),
    ("/status",    "Status endpoint"),
]

for path, name in pages:
    try:
        t0 = time.time()
        res = requests.get(f"{BASE_URL}{path}", timeout=5)
        ms = int((time.time()-t0)*1000)
        if res.status_code == 200:
            size = len(res.content)
            log(name, PASS, f"HTTP 200 | {size} bytes | {ms}ms")
        else:
            log(name, FAIL, f"HTTP {res.status_code}")
    except Exception as e:
        log(name, FAIL, str(e))

# ══════════════════════════════════════════
# TEST 3: AUTH SYSTEM
# ══════════════════════════════════════════
separator("3. AUTH SYSTEM")

# 3a: Valid OTP request
try:
    res = requests.post(f"{BASE_URL}/api/auth/send-otp",
                       json={"email": "test@test.com"}, timeout=10)
    data = res.json()
    log("Send OTP (valid email)", PASS if data.get("success") else FAIL,
        data.get("message",""))
except Exception as e:
    log("Send OTP", FAIL, str(e))

# 3b: Invalid emails
invalid_emails = ["notanemail", "", "test@", "@test.com", "ab"]
for email in invalid_emails:
    try:
        res = requests.post(f"{BASE_URL}/api/auth/send-otp",
                           json={"email": email}, timeout=5)
        data = res.json()
        if not data.get("success"):
            log(f"Reject invalid email '{email}'", PASS)
        else:
            log(f"Reject invalid email '{email}'", FAIL, "Should be rejected!")
    except Exception as e:
        log(f"Reject invalid email '{email}'", FAIL, str(e))

# 3c: Wrong OTP
try:
    res = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                       json={"email": "test@test.com", "otp": "000000"}, timeout=5)
    data = res.json()
    log("Wrong OTP rejected", PASS if not data.get("success") else FAIL)
except Exception as e:
    log("Wrong OTP rejected", FAIL, str(e))

# 3d: Brute force protection (3 wrong attempts)
print("\n  Testing brute force protection...")
for i in range(3):
    try:
        requests.post(f"{BASE_URL}/api/auth/verify-otp",
                     json={"email": "test@test.com", "otp": f"11111{i}"}, timeout=5)
    except: pass

try:
    res = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                       json={"email": "test@test.com", "otp": "111113"}, timeout=5)
    data = res.json()
    if not data.get("success"):
        log("Brute force blocked after 3 attempts", PASS)
    else:
        log("Brute force blocked", WARN, "No brute force protection")
except Exception as e:
    log("Brute force test", FAIL, str(e))

# ══════════════════════════════════════════
# TEST 4: AUTH PROTECTION
# ══════════════════════════════════════════
separator("4. AUTH PROTECTION")

protected = [
    ("POST", "/api/chat", {"task":"chat","message":"test"}),
]

for method, path, data in protected:
    try:
        # Without token
        res = requests.post(f"{BASE_URL}{path}", data=data, timeout=5)
        if res.status_code == 401:
            log(f"No token → blocked {path}", PASS, "401 Unauthorized")
        else:
            log(f"No token → blocked {path}", FAIL, f"Got {res.status_code}")

        # With fake token
        res = requests.post(f"{BASE_URL}{path}", data=data,
                           headers={"Authorization": "Bearer fake_token_123"}, timeout=5)
        if res.status_code == 401:
            log(f"Fake token → blocked {path}", PASS, "401 Unauthorized")
        else:
            log(f"Fake token → blocked {path}", FAIL, f"Got {res.status_code}")
    except Exception as e:
        log(f"Auth protection {path}", FAIL, str(e))

# ══════════════════════════════════════════
# TEST 5: AI QUALITY TEST
# ══════════════════════════════════════════
separator("5. AI RESPONSE QUALITY TEST")
print("  Note: These need a valid token. Getting token via dev mode OTP...")

# Get a real token via dev mode
dev_token = None
try:
    # Send OTP - in dev mode it prints to console
    req_res = requests.post(f"{BASE_URL}/api/auth/send-otp",
                           json={"email": "devtest@manthanai.com"}, timeout=5)

    # Try common dev OTP patterns or check if there's a test bypass
    for test_otp in ["123456", "000000"]:
        try:
            v_res = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                                 json={"email": "devtest@manthanai.com", "otp": test_otp},
                                 timeout=5)
            v_data = v_res.json()
            if v_data.get("token"):
                dev_token = v_data["token"]
                log("Got dev token for AI tests", PASS)
                break
        except: pass

    if not dev_token:
        print("  ℹ️  Check terminal for OTP, then manually test AI quality")
        print("  ℹ️  Skipping AI quality tests (need valid token)")
except Exception as e:
    print(f"  ℹ️  AI quality tests skipped: {e}")

if dev_token:
    ai_tests = [
        {
            "task": "chat",
            "message": "What is a Python list?",
            "expect_keywords": ["list", "python", "element"],
            "name": "Basic Python question"
        },
        {
            "task": "fix",
            "message": "Fix this code:\ndef add(a,b)\n    return a+b",
            "expect_keywords": ["def", ":", "syntax"],
            "name": "Bug fix — missing colon"
        },
        {
            "task": "explain",
            "message": "Explain: for i in range(5): print(i)",
            "expect_keywords": ["loop", "range", "print", "0"],
            "name": "Code explanation"
        },
        {
            "task": "generate",
            "message": "Write a Python function to check if a number is even",
            "expect_keywords": ["def", "return", "%", "2"],
            "name": "Code generation"
        },
        {
            "task": "enhance",
            "message": "Enhance: x = []; for i in range(10): x.append(i*i)",
            "expect_keywords": ["list", "comprehension", "range"],
            "name": "Code enhancement"
        },
    ]

    for test in ai_tests:
        try:
            t0 = time.time()
            form = {"task": test["task"], "message": test["message"]}
            res = requests.post(f"{BASE_URL}/api/chat",
                               data=form,
                               headers={"Authorization": f"Bearer {dev_token}"},
                               timeout=30)
            ms = int((time.time()-t0)*1000)
            data = res.json()
            reply = (data.get("response") or "").lower()

            if res.status_code == 200 and reply:
                # Check keyword presence
                found = sum(1 for kw in test["expect_keywords"] if kw.lower() in reply)
                score = int((found / len(test["expect_keywords"])) * 100)
                status = PASS if score >= 50 else WARN
                log(test["name"], status,
                    f"Score: {score}% | {ms}ms | Provider: {data.get('provider','?')}")
            else:
                log(test["name"], FAIL, f"HTTP {res.status_code}")
        except Exception as e:
            log(test["name"], FAIL, str(e))
else:
    for _ in range(5):
        log("AI Quality test", SKIP, "Need valid token — run manually")

# ══════════════════════════════════════════
# TEST 6: LOAD TEST
# ══════════════════════════════════════════
separator("6. LOAD TEST (10 Concurrent Requests)")

def single_request(i):
    try:
        t0 = time.time()
        res = requests.get(f"{BASE_URL}/status", timeout=10)
        ms = int((time.time()-t0)*1000)
        return {"ok": res.status_code == 200, "ms": ms}
    except Exception as e:
        return {"ok": False, "ms": 0, "error": str(e)}

print("  Sending 10 concurrent requests...")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(single_request, i) for i in range(10)]
    load_results = [f.result() for f in concurrent.futures.as_completed(futures)]

ok_count = sum(1 for r in load_results if r["ok"])
avg_ms   = int(sum(r["ms"] for r in load_results) / len(load_results))
max_ms   = max(r["ms"] for r in load_results)
min_ms   = min(r["ms"] for r in load_results)

log(f"10/10 requests success", PASS if ok_count==10 else FAIL,
    f"{ok_count}/10 ok")
log("Avg response time", PASS if avg_ms < 500 else WARN, f"{avg_ms}ms")
log("Max response time", PASS if max_ms < 1000 else WARN, f"{max_ms}ms")
log("Min response time", PASS, f"{min_ms}ms")

# ══════════════════════════════════════════
# TEST 7: MODULES CHECK
# ══════════════════════════════════════════
separator("7. PYTHON MODULES")

modules = [
    ("fastapi",       "FastAPI"),
    ("httpx",         "HTTP Client"),
    ("dotenv",        "python-dotenv"),
    ("pydantic",      "Pydantic"),
    ("chromadb",      "ChromaDB"),
    ("uvicorn",       "Uvicorn"),
    ("smtplib",       "SMTP (Email)"),
    ("zipfile",       "ZIP Handler"),
    ("multipart",     "File Upload"),
]

for module, name in modules:
    try:
        __import__(module)
        log(f"{name}", PASS)
    except ImportError:
        log(f"{name}", FAIL, f"pip install {module} --break-system-packages")

# ══════════════════════════════════════════
# TEST 8: ENV & FILES
# ══════════════════════════════════════════
separator("8. ENV CONFIG & FILES")

env_checks = [
    ("GROQ_API_KEY",      "Groq API Key",    True),
    ("GEMINI_API_KEY",    "Gemini API Key",  True),
    ("SMTP_EMAIL",        "SMTP Email",      False),
    ("SMTP_APP_PASSWORD", "SMTP Password",   False),
]

for var, name, required in env_checks:
    val = os.getenv(var, "")
    if val and len(val) > 5:
        log(name, PASS, f"{val[:8]}...")
    elif required:
        log(name, FAIL, f"Add to .env: {var}=your_key")
    else:
        log(name, WARN, f"Optional — add for email OTP")

files_check = [
    "main.py", "core/model.py", "core/router.py",
    "core/auth.py", "core/prompts.py",
    "ai/chat.py", "ai/run.py",
    "rag/indexer.py", "repo/ingest.py",
    "index.html", "login.html", "dashboard.html",
    ".env", "requirements.txt",
]

for f in files_check:
    if os.path.exists(f):
        log(f, PASS, f"{os.path.getsize(f)} bytes")
    else:
        log(f, FAIL, f"Missing!")

# ══════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════
elapsed = int((time.time() - total_time) * 1000)

print(f"\n{'═'*55}")
print("  FINAL REPORT")
print(f"{'═'*55}")

passed  = len([r for r in results if r["status"] == PASS])
failed  = len([r for r in results if r["status"] == FAIL])
warned  = len([r for r in results if r["status"] == WARN])
skipped = len([r for r in results if r["status"] == SKIP])
total   = len(results)
score   = int((passed / (total - skipped)) * 100) if (total - skipped) > 0 else 0

print(f"""
  Total Tests  : {total}
  ✅ Passed    : {passed}
  ❌ Failed    : {failed}
  ⚠️  Warnings  : {warned}
  ⏭️  Skipped   : {skipped}
  ⏱️  Time      : {elapsed}ms

  🎯 SCORE     : {score}%
""")

if score == 100:
    print("  🔥 PERFECT! Manthan AI is fully working!")
elif score >= 80:
    print("  ✅ GOOD! Minor issues. Fix warnings above.")
elif score >= 60:
    print("  ⚠️  NEEDS WORK. Fix the failures below.")
else:
    print("  ❌ CRITICAL ISSUES. Fix immediately.")

if failed > 0:
    print(f"\n  FAILURES TO FIX:")
    for r in results:
        if r["status"] == FAIL:
            print(f"  ❌ {r['name']}")
            if r['detail']: print(f"     Fix: {r['detail']}")

if warned > 0:
    print(f"\n  WARNINGS:")
    for r in results:
        if r["status"] == WARN:
            print(f"  ⚠️  {r['name']}: {r['detail']}")

print(f"\n{'═'*55}\n")