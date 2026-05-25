"""
WhatsApp AI Auto-Reply - AI Microservice (Enhanced with Full Dashboard API)

Provides:
- AI-powered WhatsApp auto-reply via multiple providers
- Guard rails filtering (profanity, PII, topics, rate limits)
- Approval queue for human-in-the-loop moderation
- Full REST API for admin dashboard
- Persistent logging and message history
"""

import os, sys, json, time, httpx, traceback, asyncio, logging, signal
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, Literal
from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from guard_rails import GuardRailsEngine
import logs_store
import message_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("whatsapp_ai")

# ===== Provider Configurations =====
PROVIDERS = {
    "ollama": {
        "models": ["llama3.2:1b", "llama3.1:8b", "mistral", "gemma2", "phi3", "llama3:70b"],
        "default_base_url": "http://host.docker.internal:11434"
    },
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_base_url": "https://api.openai.com/v1"
    },
    "anthropic": {
        "models": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "default_base_url": "https://api.anthropic.com/v1"
    },
    "google": {
        "models": ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
        "default_base_url": "https://generativelanguage.googleapis.com/v1"
    },
    "groq": {
        "models": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        "default_base_url": "https://api.groq.com/openai/v1"
    },
    "cohere": {
        "models": ["command-r", "command-r-plus", "command-light"],
        "default_base_url": "https://api.cohere.ai/v1"
    },
    "mistral": {
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"],
        "default_base_url": "https://api.mistral.ai/v1"
    },
    "together": {
        "models": ["mistralai/Mixtral-8x7B-Instruct-v0.1", "togethercomputer/llama-2-70b-chat"],
        "default_base_url": "https://api.together.xyz/v1"
    },
    "deepseek": {
        "models": ["deepseek-chat", "deepseek-coder"],
        "default_base_url": "https://api.deepseek.com/v1"
    },
    "perplexity": {
        "models": ["llama-3-sonar-small-32k", "llama-3-sonar-large-32k"],
        "default_base_url": "https://api.perplexity.ai"
    },
    "openrouter": {
        "models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3-70b-instruct"],
        "default_base_url": "https://openrouter.ai/api/v1"
    }
}


# ===== Environment Variables =====
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://waha:3000")
WHATSAPP_SESSION = os.getenv("WHATSAPP_SESSION", "default")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful WhatsApp assistant. Keep replies short, friendly and professional.")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "300"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# ===== Global State =====
start_time = time.time()
last_ai_error = None
last_ai_request_time = 0
restart_requested = False

approval_queue = []


def load_ai_config():
    config_path = os.path.expanduser("/root/.whatsapp_ai_config.json")
    defaults = {
        "provider": "ollama",
        "model": "llama3.2:1b",
        "base_url": "http://host.docker.internal:11434",
        "api_key": "",
        "temperature": AI_TEMPERATURE,
        "max_tokens": AI_MAX_TOKENS,
        "system_prompt": SYSTEM_PROMPT
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                loaded = json.load(f)
                defaults.update(loaded)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    return defaults


def save_ai_config(config: dict):
    config_path = os.path.expanduser("/root/.whatsapp_ai_config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


ai_config = load_ai_config()
guard = GuardRailsEngine()

# Wrapper methods for dashboard compatibility
def _guard_pre_filter(text):
    result = guard.process_incoming("global", text)
    return result.get("reason") if result.get("blocked") else None

def _guard_post_filter(text):
    result = guard.process_outgoing("global", text)
    if result.get("blocked"):
        return result.get("reason", "Blocked by guard rails")
    return None

guard.pre_filter = _guard_pre_filter
guard.post_filter = _guard_post_filter

# Add missing attributes for dashboard read/write
guard.profanity_block = True
guard.pii_detection = True
guard.topic_blacklist = True
guard.enabled = True
if hasattr(guard, 'profanity'):
    guard.profanity_filter = guard.profanity
if hasattr(guard, 'topics'):
    guard.topic_filter = guard.topics


# ===== Pydantic Models =====
class SendMessageRequest(BaseModel):
    phone: str
    message: str

class ApproveRequest(BaseModel):
    index: int
    action: Literal["approve", "reject"]

class AIProviderConfig(BaseModel):
    provider: str = "ollama"
    model: str = "llama3.2:1b"
    base_url: str = "http://host.docker.internal:11434"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 300
    system_prompt: str = "You are a helpful WhatsApp assistant."

class SettingsModel(BaseModel):
    waaha_base_url: str = "http://waha:3000"
    whatsapp_session: str = "default"
    system_prompt: str = "You are a helpful WhatsApp assistant."
    max_chars: int = 500
    rate_limit_per_minute: int = 10
    rate_limit_cooldown: float = 10.0
    approval_mode: bool = False

class GuardRailsConfig(BaseModel):
    enabled: bool = True
    profanity_block: bool = True
    pii_detection: bool = True
    topic_blacklist: bool = True
    max_chars: int = 500
    rate_limit_per_minute: int = 10
    rate_limit_cooldown: float = 10.0
    custom_blocked_words: list[str] = []
    custom_blocked_topics: list[str] = []

# ===== AI Provider Functions =====


async def call_ai(prompt: str, conversation_history: list = None) -> tuple[Optional[str], Optional[str]]:
    """Call the AI provider with the given prompt. Returns (response_text, error_message)."""
    global last_ai_error, last_ai_request_time
    config = load_ai_config()
    provider = config["provider"]
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "")
    model = config.get("model", "llama3.2:1b")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 300)
    system_prompt = config.get("system_prompt", SYSTEM_PROMPT)
    last_ai_request_time = time.time()
    last_ai_error = None
    try:
        if provider == "ollama":
            return await _call_ollama(base_url, model, prompt, system_prompt, conversation_history)
        elif provider in ("openai", "groq", "together", "deepseek", "perplexity", "openrouter"):
            return await _call_openai_compat(provider, base_url, model, api_key, prompt, system_prompt, conversation_history, temperature, max_tokens)
        elif provider == "anthropic":
            return await _call_anthropic(base_url, model, api_key, prompt, system_prompt, conversation_history, temperature, max_tokens)
        elif provider == "google":
            return await _call_google(base_url, model, api_key, prompt, system_prompt, conversation_history, temperature, max_tokens)
        elif provider == "cohere":
            return await _call_cohere(base_url, model, api_key, prompt, system_prompt, conversation_history, temperature, max_tokens)
        elif provider == "mistral":
            return await _call_mistral(base_url, model, api_key, prompt, system_prompt, conversation_history, temperature, max_tokens)
        else:
            return None, f"Unknown provider: {provider}"
    except Exception as e:
        err_msg = f"AI call failed: {str(e)}"
        last_ai_error = err_msg
        logs_store.add_log("error", "ai_service", err_msg, details={"provider": provider, "model": model})
        logger.error(traceback.format_exc())
        return None, err_msg


async def _call_ollama(base_url, model, prompt, system_prompt, conversation_history=None):
    """Call Ollama API for chat completion."""
    url = f"{base_url.rstrip('/')}/api/chat"
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "assistant" if msg.get("direction") == "outgoing" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "stream": False}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", {}).get("content", ""), None
        else:
            return None, f"Ollama error {resp.status_code}: {resp.text}"


async def _call_openai_compat(provider_name, base_url, model, api_key, prompt, system_prompt, conversation_history=None, temperature=0.7, max_tokens=300):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "assistant" if msg.get("direction") == "outgoing" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"], None
        else:
            return None, f"{provider_name} error {resp.status_code}: {resp.text}"


async def _call_anthropic(base_url, model, api_key, prompt, system_prompt, conversation_history=None, temperature=0.7, max_tokens=300):
    url = f"{base_url.rstrip('/')}/messages"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    messages = []
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "assistant" if msg.get("direction") == "outgoing" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "system": system_prompt, "temperature": temperature, "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"], None
        else:
            return None, f"Anthropic error {resp.status_code}: {resp.text}"


async def _call_google(base_url, model, api_key, prompt, system_prompt, conversation_history=None, temperature=0.7, max_tokens=300):
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
    contents = []
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "model" if msg.get("direction") == "outgoing" else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"], None
            return None, "No response from Google AI"
        else:
            return None, f"Google error {resp.status_code}: {resp.text}"


async def _call_cohere(base_url, model, api_key, prompt, system_prompt, conversation_history=None, temperature=0.7, max_tokens=300):
    url = f"{base_url.rstrip('/')}/chat"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    chat_history = []
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "CHATBOT" if msg.get("direction") == "outgoing" else "USER"
            chat_history.append({"role": role, "message": msg.get("content", "")})
    payload = {"model": model, "message": prompt, "chat_history": chat_history, "preamble": system_prompt, "temperature": temperature, "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data["text"], None
        else:
            return None, f"Cohere error {resp.status_code}: {resp.text}"


async def _call_mistral(base_url, model, api_key, prompt, system_prompt, conversation_history=None, temperature=0.7, max_tokens=300):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "assistant" if msg.get("direction") == "outgoing" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"], None
        else:
            return None, f"Mistral error {resp.status_code}: {resp.text}"


async def call_ai_with_reply(phone: str, incoming_text: str, chat_history: list = None):
    """Generate an AI reply for an incoming message."""
    pre_result = guard.pre_filter(incoming_text)
    if pre_result:
        logs_store.add_log("warning", "guard_rails", f"Message blocked: {pre_result}", details={"phone": phone, "text": incoming_text[:200]})
        message_history.add_message(phone, phone, "system", incoming_text, direction="incoming", status="blocked")
        return False, pre_result
    message_history.add_message(phone, phone, "system", incoming_text, direction="incoming", status="received")
    logs_store.add_log("info", "message", f"Incoming message from {phone}", details={"text": incoming_text[:200]})
    reply_text, error = await call_ai(incoming_text, chat_history)
    if error:
        logs_store.add_log("error", "ai_service", f"AI reply failed for {phone}: {error}")
        return False, error
    post_result = guard.post_filter(reply_text)
    if post_result:
        logs_store.add_log("warning", "guard_rails", f"AI reply blocked: {post_result}", details={"phone": phone, "reply": reply_text[:200]})
        message_history.add_message(phone, phone, "system", reply_text, direction="outgoing", status="blocked")
        return False, post_result
    if guard.approval_mode:
        approval_queue.append({
            "phone": phone,
            "incoming": incoming_text,
            "reply": reply_text,
            "timestamp": time.time(),
            "status": "pending"
        })
        logs_store.add_log("info", "approval", f"Reply queued for approval: {phone}")
        message_history.add_message(phone, phone, "system", reply_text, direction="outgoing", status="pending")
        return True, "queued_for_approval"
    success, err = await send_whatsapp_message(phone, reply_text)
    if success:
        message_history.add_message(phone, phone, "system", reply_text, direction="outgoing", status="sent")
        logs_store.add_log("info", "message", f"Reply sent to {phone}")
        return True, reply_text
    else:
        logs_store.add_log("error", "waha", f"Failed to send reply to {phone}: {err}")
        message_history.add_message(phone, phone, "system", reply_text, direction="outgoing", status="failed")
        return False, err


async def send_whatsapp_message(phone: str, message: str) -> tuple[bool, Optional[str]]:
    """Send a WhatsApp message via WAHA API."""
    try:
        url = f"{WAHA_BASE_URL.rstrip('/')}/api/sendText"
        headers = {"Content-Type": "application/json"}
        waha_api_key = os.getenv("WAHA_API_KEY", "waha-whatsapp-ai-secret-key-2026")
        if waha_api_key:
            headers["X-Api-Key"] = waha_api_key
        payload = {"session": WHATSAPP_SESSION, "chatId": phone, "text": message}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                return True, None
            else:
                return False, f"WAHA error {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, str(e)
# ===== FastAPI App =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("WhatsApp AI Service starting...")
    logs_store.add_log("info", "system", "Service started");
    yield
    logger.info("WhatsApp AI Service shutting down...");

app = FastAPI(title="WhatsApp AI Auto-Reply", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]);

# ===== HELPER: Check approval mode =====
approval_mode = lambda: getattr(guard, "approval_mode", False);


# ============ API ENDPOINTS ============

# 1. Health Check
@app.get("/health")
async def health_check():
    return {"status": "ok", "uptime": round(time.time() - start_time, 1)};


# 2. Webhook endpoints
@app.post("/webhook/message/raw")
async def webhook_raw(request: Request):
    """Primary WAHA webhook endpoint."""
    try:
        payload = await request.json()
        if isinstance(payload, list):
            for item in payload:
                asyncio.create_task(process_webhook_payload(item))
        else:
            asyncio.create_task(process_webhook_payload(payload))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}


@app.post("/webhook/message")
async def webhook_alt(request: Request):
    """Alternative webhook endpoint for different payload formats."""
    try:
        data = await request.json()
        payload = data.get("payload", data)
        message = payload.get("message", {})
        if isinstance(message, dict):
            text = message.get("text", "")
        else:
            text = str(message) if message else ""
        chat_id = payload.get("chatId", payload.get("from", "unknown"))
        from_me = payload.get("fromMe", False)
        if not from_me and text.strip():
            asyncio.create_task(call_ai_with_reply(chat_id, str(text)))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}


async def process_webhook_payload(payload: dict):
    """Process a single webhook payload."""
    try:
        messages = payload.get("messages", [payload.get("message", payload)])
        if not isinstance(messages, list):
            messages = [messages]
        for msg in messages:
            if isinstance(msg, dict):
                text = msg.get("text", {}).get("text", msg.get("body", ""))
                if isinstance(text, dict):
                    text = text.get("text", "")
                chat_id = msg.get("from", msg.get("chatId", "unknown"))
                from_me = msg.get("fromMe", False)
                if not from_me and str(text).strip() and chat_id != "unknown":
                    asyncio.create_task(call_ai_with_reply(chat_id, str(text)))
    except Exception as e:
        logger.error(f"Payload processing error: {e}")


# 3. Send Message
@app.post("/send")
@app.post("/api/send")
async def send_message(data: SendMessageRequest):
    """Send a WhatsApp message manually."""
    if not data.phone or len(data.phone) < 5:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    if not data.message or len(data.message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    success, err = await send_whatsapp_message(data.phone, data.message)
    if success:
        message_history.add_message(data.phone, data.phone, "system", data.message, direction="outgoing", status="sent")
        logs_store.add_log("info", "message", f"Manual message sent to {data.phone}")
        return {"status": "sent"}
    else:
        raise HTTPException(status_code=500, detail=err)


# 4. Guard Queue / Approval
@app.get("/guard-queue")
async def get_guard_queue():
    """Get all items pending approval."""
    result = []
    for i, item in enumerate(approval_queue):
        result.append({
            "index": i,
            "phone": item["phone"],
            "incoming": item["incoming"],
            "reply": item["reply"],
            "timestamp": item["timestamp"],
            "status": item["status"]
        })
    return {"queue": result, "count": len(result)}


@app.post("/guard-queue/approve")
async def approve_item(data: ApproveRequest):
    """Approve or reject a queued message."""
    if data.index < 0 or data.index >= len(approval_queue):
        raise HTTPException(status_code=404, detail="Item not found")
    item = approval_queue[data.index]
    if data.action == "approve":
        item["status"] = "approved"
        success, err = await send_whatsapp_message(item["phone"], item["reply"])
        if success:
            message_history.add_message(item["phone"], item["phone"], "system", item["reply"], direction="outgoing", status="sent")
            logs_store.add_log("info", "approval", f"Reply approved and sent to {item["phone"]}")
            approval_queue.pop(data.index)
            return {"status": "approved", "action": "sent"}
        else:
            return {"status": "approved", "action": "send_failed", "error": err}
    else:
        item["status"] = "rejected"
        logs_store.add_log("info", "approval", f"Reply rejected for {item["phone"]}")
        approval_queue.pop(data.index)
        return {"status": "rejected"}


# ============ DASHBOARD API ENDPOINTS ============

# 5. Providers
@app.get("/api/providers")
async def get_providers():
    """List providers with their available models."""
    result = {}
    for name, cfg in PROVIDERS.items():
        result[name] = {"models": cfg["models"], "default_base_url": cfg["default_base_url"]}
    return result


# 6. AI Provider Settings
@app.get("/api/settings/ai")
async def get_ai_settings():
    """Get AI provider configuration."""
    return load_ai_config()


@app.put("/api/settings/ai")
async def update_ai_settings(config: AIProviderConfig):
    """Update AI provider configuration."""
    new_config = config.model_dump()
    save_ai_config(new_config)
    global ai_config
    ai_config = load_ai_config()
    logs_store.add_log("info", "settings", f"AI config updated: {config.provider}/{config.model}")
    return {"status": "saved", "config": ai_config}


@app.post("/api/settings/ai/test")
async def test_ai_connection(config: AIProviderConfig):
    """Test AI provider connection."""
    old_config = ai_config.copy()
    ai_config.update(config.model_dump())
    try:
        reply, error = await call_ai("Reply with only the word: OK")
        if error:
            return {"status": "error", "message": error}
        return {"status": "success", "reply": reply}
    finally:
        ai_config.update(old_config)


# 7. General Settings
@app.get("/api/settings")
async def get_settings():
    """Get all general settings."""
    return {
        "waaha_base_url": WAHA_BASE_URL,
        "whatsapp_session": WHATSAPP_SESSION,
        "system_prompt": SYSTEM_PROMPT,
        "max_chars": getattr(guard, "max_chars", 500),
        "rate_limit_per_minute": getattr(guard, "rate_limit_per_minute", 10),
        "rate_limit_cooldown": getattr(guard, "rate_limit_cooldown", 10.0),
        "approval_mode": getattr(guard, "approval_mode", False)
    }


@app.put("/api/settings")
async def update_settings(settings: SettingsModel):
    """Update general settings."""
    global WAHA_BASE_URL, WHATSAPP_SESSION, SYSTEM_PROMPT
    WAHA_BASE_URL = settings.waaha_base_url
    WHATSAPP_SESSION = settings.whatsapp_session
    SYSTEM_PROMPT = settings.system_prompt
    guard.max_chars = settings.max_chars
    guard.rate_limit_per_minute = settings.rate_limit_per_minute
    guard.rate_limit_cooldown = settings.rate_limit_cooldown
    guard.approval_mode = settings.approval_mode
    logs_store.add_log("info", "settings", "General settings updated")
    return {"status": "saved"}


# 8. Guard Rails Settings
@app.get("/api/settings/guardrails")
async def get_guardrails_settings():
    """Get guard rails configuration."""
    return {
        "enabled": getattr(guard, "enabled", True),
        "profanity_block": getattr(guard, "profanity_block", True),
        "pii_detection": getattr(guard, "pii_detection", True),
        "topic_blacklist": getattr(guard, "topic_blacklist", True),
        "max_chars": getattr(guard, "max_chars", 500),
        "rate_limit_per_minute": getattr(guard, "rate_limit_per_minute", 10),
        "rate_limit_cooldown": getattr(guard, "rate_limit_cooldown", 10.0),
        "custom_blocked_words": getattr(guard, "custom_blocked_words", []),
        "custom_blocked_topics": getattr(guard, "custom_blocked_topics", [])
    }


@app.put("/api/settings/guardrails")
async def update_guardrails_settings(config: GuardRailsConfig):
    """Update guard rails configuration."""
    guard.enabled = config.enabled
    guard.profanity_block = config.profanity_block
    guard.pii_detection = config.pii_detection
    guard.topic_blacklist = config.topic_blacklist
    guard.max_chars = config.max_chars
    guard.rate_limit_per_minute = config.rate_limit_per_minute
    guard.rate_limit_cooldown = config.rate_limit_cooldown
    if hasattr(guard, "profanity_filter") and guard.profanity_filter and config.custom_blocked_words:
        guard.profanity_filter.words = config.custom_blocked_words
    if hasattr(guard, "topic_filter") and guard.topic_filter and config.custom_blocked_topics:
        guard.topic_filter.topics = config.custom_blocked_topics
    logs_store.add_log("info", "settings", "Guard rails config updated")
    return {"status": "saved"}


# 9. Logs
@app.get("/api/logs")
async def get_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    level: str = Query(None),
    source: str = Query(None),
    search: str = Query(None),
    from_date: str = Query(None),
    to_date: str = Query(None)
):
    """Get paginated logs."""
    return logs_store.get_logs(
        page=page, per_page=per_page,
        level=level, source=source, search=search,
        from_date=from_date, to_date=to_date
    )


@app.get("/api/logs/{log_id}")
async def get_log_detail(log_id: int):
    """Get a single log entry."""
    log = logs_store.get_log_by_id(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@app.delete("/api/logs")
async def clear_logs():
    """Clear all logs."""
    logs_store.clear_logs()
    logs_store.add_log("info", "system", "Logs cleared by user")
    return {"status": "cleared"}


@app.get("/api/logs/stats")
async def get_log_stats():
    """Get log statistics."""
    return logs_store.get_log_stats()


# 10. Messages
@app.get("/api/messages")
async def get_messages(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    phone: str = Query(None),
    direction: str = Query(None),
    status: str = Query(None)
):
    """Get message history."""
    return message_history.get_messages(
        page=page, per_page=per_page,
        phone=phone, direction=direction, status=status
    )


@app.get("/api/messages/{phone}")
async def get_conversation(phone: str, limit: int = Query(50, ge=1, le=500)):
    """Get conversation with a phone number."""
    return message_history.get_conversation(phone, limit)


@app.delete("/api/messages")
async def clear_messages_route():
    """Clear all message history."""
    message_history.clear_messages()
    logs_store.add_log("info", "system", "Message history cleared by user")
    return {"status": "cleared"}


# 11. WhatsApp Status
@app.get("/api/whatsapp/status")
async def get_whatsapp_status():
    """Get WAHA connection status."""
    try:
        waha_api_key = os.getenv("WAHA_API_KEY", "waha-whatsapp-ai-secret-key-2026")
        headers = {"X-Api-Key": waha_api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WAHA_BASE_URL.rstrip('/')}/api/sessions/{WHATSAPP_SESSION}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return {"status": "connected", "details": data}
            else:
                return {"status": "disconnected", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 12. Dashboard Stats
@app.get("/api/stats")
async def get_dashboard_stats():
    """Get dashboard statistics."""
    msg_stats = message_history.get_message_stats()
    log_stats = logs_store.get_log_stats()
    active_convs = message_history.get_active_conversations()
    approval_count = len(approval_queue)
    uptime = round(time.time() - start_time, 1)
    return {
        "messages_today": msg_stats.get("total", 0),
        "blocked_today": msg_stats.get("blocked", 0),
        "ai_replies_today": msg_stats.get("outgoing", 0),
        "approval_queue": approval_count,
        "active_conversations": len(active_convs),
        "uptime_seconds": uptime,
        "total_messages": msg_stats.get("total", 0),
        "total_logs": log_stats.get("total", 0)
    }


# 13. System endpoints
@app.post("/api/system/retry")
async def retry_last_ai():
    """Retry the last failed AI request."""
    global last_ai_error
    if not last_ai_error:
        return {"status": "no_error", "message": "No previous error to retry"}
    last_ai_error = None
    logs_store.add_log("info", "system", "Retry requested for last AI failure")
    return {"status": "retrying", "message": "Last error cleared. Next request will retry."}


@app.post("/api/system/restart")
async def restart_service():
    """Gracefully restart the service."""
    global restart_requested
    restart_requested = True
    logs_store.add_log("info", "system", "Restart requested")
    async def _restart(): await asyncio.sleep(1); os._exit(0)
    asyncio.create_task(_restart())
    return {"status": "restarting"}


# ===== Error Handlers =====
@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse({"error": exc.detail, "status_code": exc.status_code}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    logs_store.add_log("error", "system", f"Unhandled error: {str(exc)}", details={"path": str(request.url)})
    return JSONResponse({"error": "Internal server error"}, status_code=500)


# ===== Main Entry =====
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)