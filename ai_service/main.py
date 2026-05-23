"""
WhatsApp AI Auto-Reply - AI Microservice

FastAPI service that:
1. Waits for webhook callbacks from WAHA WhatsApp API
2. Runs incoming message through guard rails
3. Generates AI reply via Ollama or OpenAI
4. Sends reply back through WAHA API
"""
import os
import httpx
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from guard_rails import GuardRailsEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("whatsapp_ai")

# ========== Configuration ==========
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://waha:3000")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")  # "ollama" or "openai"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "150"))
WHATSAPP_SESSION = os.getenv("WHATSAPP_SESSION", "default")

# Guard rails configuration
GUARD_CONFIG = {
    "max_chars": int(os.getenv("MAX_CHARS", "500")),
    "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
    "rate_limit_cooldown": float(os.getenv("RATE_LIMIT_COOLDOWN", "10.0")),
    "approval_mode": os.getenv("APPROVAL_MODE", "false").lower() == "true",
}

guard = GuardRailsEngine(GUARD_CONFIG)

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful WhatsApp assistant. Keep replies short, friendly and "
    "professional. Never share personal info. Never discuss restricted topics. "
    "If asked about something you cannot answer, politely decline."
)


# ========== Lifespan ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WhatsApp AI Microservice starting...")
    logger.info(f"AI Provider: {AI_PROVIDER}")
    logger.info(f"WhatsApp API: {WAHA_BASE_URL}")
    yield
    logger.info("WhatsApp AI Microservice shutting down...")


app = FastAPI(
    title="WhatsApp AI Auto-Reply Service",
    version="1.0.0",
    lifespan=lifespan,
)


# ========== Models ==========

class IncomingMessage(BaseModel):
    """Payload from WAHA webhook."""
    chatId: str = Field(..., description="WhatsApp chat ID (phone@c.us)")
    text: str = Field("", description="Message text content")
    fromMe: bool = Field(False, description="Whether this message was sent by the session itself")
    id: str = Field("", description="Message ID for deduplication")
    timestamp: int = Field(0, description="Unix timestamp")


class SendMessageRequest(BaseModel):
    chatId: str
    text: str
    session: str = WHATSAPP_SESSION


class HealthResponse(BaseModel):
    status: str
    ai_provider: str
    guard_rails: dict


# ========== Helper Functions ==========

async def generate_ai_reply(user_message: str) -> str:
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not set, falling back to Ollama")
            return await _ollama_reply(user_message)
        return await _openai_reply(user_message)
    else:
        return await _ollama_reply(user_message)


async def _ollama_reply(user_message: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": f"{SYSTEM_PROMPT}\n\nUser message: {user_message}\n\nReply:",
            "stream": False,
            "options": {
                "temperature": AI_TEMPERATURE,
                "num_predict": AI_MAX_TOKENS,
            }
        }
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("response", "").strip()
            return reply if reply else "I'm sorry, I couldn't process that request."
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return "I'm sorry, the AI service is temporarily unavailable."


async def _openai_reply(user_message: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
        )
        reply = resp.choices[0].message.content.strip()
        return reply if reply else "I'm sorry, I couldn't process that request."
    except Exception as e:
        logger.error(f"OpenAI request failed: {e}")
        return "I'm sorry, the AI service is temporarily unavailable."


async def send_whatsapp_message(chat_id: str, text: str) -> dict:
    url = f"{WAHA_BASE_URL}/api/sendText"
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": WHATSAPP_SESSION,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


# ========== Endpoints ==========

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        ai_provider=AI_PROVIDER,
        guard_rails={
            "max_chars": GUARD_CONFIG["max_chars"],
            "rate_limit_per_minute": GUARD_CONFIG["rate_limit_per_minute"],
            "per_chat_cooldown_seconds": GUARD_CONFIG["rate_limit_cooldown"],
            "approval_mode": GUARD_CONFIG["approval_mode"],
        }
    )


@app.post("/webhook/message")
async def handle_incoming_message(msg: IncomingMessage):
    logger.info(f"Received message from {msg.chatId}: {msg.text[:80]}...")

    if msg.fromMe:
        logger.debug("Skipping own message")
        return {"status": "skipped", "reason": "own_message"}

    if not msg.text.strip():
        logger.debug("Skipping empty message")
        return {"status": "skipped", "reason": "empty"}

    # Guard Rails: Incoming Check
    check = guard.process_incoming(msg.chatId, msg.text)
    if check["blocked"]:
        logger.warning(f"Incoming blocked: {check['reason']}")
        return {"status": "blocked", "reason": check["reason"]}

    # Generate AI Reply
    reply = await generate_ai_reply(msg.text)
    logger.info(f"AI reply generated ({len(reply)} chars)")

    # Guard Rails: Outgoing Check
    check = guard.process_outgoing(msg.chatId, reply)
    if check["blocked"]:
        reason = check.get("reason", "Blocked by guard rails")
        logger.warning(f"Outgoing blocked: {reason}")
        if check.get("queued"):
            return {"status": "queued", "reason": "Awaiting human approval"}
        reply = "I'm sorry, I cannot reply to that at the moment."

    # Send Reply
    try:
        result = await send_whatsapp_message(msg.chatId, reply)
        logger.info(f"Reply sent to {msg.chatId}")
        return {"status": "sent", "reply": reply[:80] + "..."}
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/message/raw")
async def handle_raw_webhook(request: Request):
    try:
        payload = await request.json()
        logger.debug(f"Raw webhook received: {json.dumps(payload)[:200]}...")

        if "payload" in payload:
            payload = payload["payload"]

        chat_id = payload.get("chatId") or payload.get("from") or payload.get("chat_id", "")
        text = payload.get("text") or payload.get("body") or payload.get("message", "")
        from_me = payload.get("fromMe", False)

        msg = IncomingMessage(
            chatId=chat_id,
            text=text if isinstance(text, str) else str(text),
            fromMe=from_me,
            id=payload.get("id", ""),
            timestamp=payload.get("timestamp", 0),
        )

        return await handle_incoming_message(msg)
    except Exception as e:
        logger.error(f"Failed to parse raw webhook: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/send")
async def send_message(req: SendMessageRequest):
    try:
        result = await send_whatsapp_message(req.chatId, req.text)
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/guard-queue")
async def get_approval_queue():
    return {
        "queue_length": len(guard.approval_queue),
        "items": guard.approval_queue[-20:]
    }


@app.post("/guard-queue/approve")
async def approve_queue_item(index: int):
    if index >= len(guard.approval_queue):
        raise HTTPException(status_code=404, detail="Item not found")
    item = guard.approval_queue.pop(index)
    try:
        result = await send_whatsapp_message(item["chat_id"], item["reply"])
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
