# ============================================
# MANTHAN AI — Code Run Endpoint
# File: ai/run.py
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.router import ask_ai
from core.prompts import get_system_prompt
import subprocess, tempfile, os

router = APIRouter()

class RunRequest(BaseModel):
    code: str
    language: str = "python"
    explain_errors: bool = True

class RunResponse(BaseModel):
    output: str
    error: str
    success: bool
    explanation: str = ""

LANG_CONFIG = {
    "python":     {"ext": ".py",  "cmd": ["python3"]},
    "javascript": {"ext": ".js",  "cmd": ["node"]},
}

@router.post("/run", response_model=RunResponse)
async def run_code(req: RunRequest):
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Code empty hai!")

    lang = req.language.lower()
    if lang not in LANG_CONFIG:
        raise HTTPException(status_code=400, detail=f"Language '{lang}' supported nahi. Use: {list(LANG_CONFIG.keys())}")

    config = LANG_CONFIG[lang]

    with tempfile.NamedTemporaryFile(mode="w", suffix=config["ext"], delete=False) as f:
        f.write(req.code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            config["cmd"] + [tmp_path],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        error  = result.stderr.strip()
        success = result.returncode == 0

        explanation = ""
        if error and req.explain_errors:
            try:
                ai_result = await ask_ai(
                    task="fix",
                    user_message=f"Code:\n{req.code}\n\nError:\n{error}",
                    system_prompt=get_system_prompt("fix")
                )
                explanation = ai_result["response"]
            except Exception:
                explanation = "AI explanation unavailable."

        return RunResponse(output=output, error=error, success=success, explanation=explanation)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Code 15 seconds me complete nahi hua!")
    finally:
        os.unlink(tmp_path)
