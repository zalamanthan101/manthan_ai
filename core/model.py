# ============================================
# MANTHAN AI — AI Provider Configuration
# File: core/model.py
# ============================================

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ProviderConfig:
    name: str
    api_key: str
    model_id: str
    base_url: str
    is_free: bool

PROVIDERS = {
    "gemini": ProviderConfig(
        name="Google Gemini",
        api_key=os.getenv("GEMINI_API_KEY", ""),
        model_id="gemini-2.0-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        is_free=True
    ),
    "groq": ProviderConfig(
        name="Groq",
        api_key=os.getenv("GROQ_API_KEY", ""),
        model_id="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        is_free=True
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model_id="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        is_free=False
    ),
}

TASK_PROVIDER_MAP = {
    "chat":     "groq",
    "fix":      "groq",
    "explain":  "groq",
    "enhance":  "groq",
    "review":   "groq",
    "generate": "groq",
}

def get_provider(task: str) -> ProviderConfig:
    provider_key = TASK_PROVIDER_MAP.get(task, "groq")
    provider = PROVIDERS[provider_key]

    if not provider.api_key:
        for p in PROVIDERS.values():
            if p.api_key:
                return p
        raise ValueError("Koi bhi API key nahi mili! .env file check karo.")

    return provider