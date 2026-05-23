"""
Guard Rails Engine for WhatsApp AI Auto-Reply

Provides content filtering, PII detection, rate limiting, and safety checks
for AI-generated WhatsApp replies.
"""
import re
import time
import logging
from typing import Optional

logger = logging.getLogger("guard_rails")


class ProfanityFilter:
    def __init__(self, words: list[str] = None):
        self.words = words or [
            "spam", "scam", "click here", "free money",
            "you've won", "congratulations you won",
            "buy now", "limited offer", "act now",
        ]
        self.patterns = [re.compile(re.escape(w), re.IGNORECASE) for w in self.words]

    def is_blocked(self, text: str) -> Optional[str]:
        for i, pat in enumerate(self.patterns):
            if pat.search(text):
                return f"Profanity/Spam trigger: '{self.words[i]}'"
        return None


class PIIDetector:
    def __init__(self):
        self.patterns = {
            "email": re.compile(r'[\w.-]+@[\w.-]+\.\w+'),
            "phone": re.compile(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        }

    def has_pii(self, text: str) -> Optional[str]:
        for name, pat in self.patterns.items():
            if pat.search(text):
                return f"PII detected: {name}"
        return None


class TopicBlacklist:
    def __init__(self, topics: list[str] = None):
        self.topics = topics or [
            "politics", "election", "candidate", "vote",
            "illegal", "weapons", "drugs", "gambling",
            "pornography", "hacking", "crack", "keygen",
        ]
        self.patterns = [re.compile(re.escape(t), re.IGNORECASE) for t in self.topics]

    def is_blocked(self, text: str) -> Optional[str]:
        for i, pat in enumerate(self.patterns):
            if pat.search(text):
                return f"Topic blacklisted: '{self.topics[i]}'"
        return None


class RateLimiter:
    def __init__(self, max_per_minute: int = 10, per_chat_cooldown: float = 10.0):
        self.max_per_minute = max_per_minute
        self.per_chat_cooldown = per_chat_cooldown
        self.global_timestamps: list[float] = []
        self.chat_timestamps: dict[str, float] = {}

    def check_global(self) -> Optional[str]:
        now = time.time()
        window_start = now - 60
        self.global_timestamps = [t for t in self.global_timestamps if t > window_start]
        if len(self.global_timestamps) >= self.max_per_minute:
            return "Global rate limit exceeded (max 10/min)"
        self.global_timestamps.append(now)
        return None

    def check_chat(self, chat_id: str) -> Optional[str]:
        now = time.time()
        last = self.chat_timestamps.get(chat_id, 0)
        if now - last < self.per_chat_cooldown:
            remaining = int(self.per_chat_cooldown - (now - last))
            return f"Chat rate limit: wait {remaining}s before next reply"
        self.chat_timestamps[chat_id] = now
        return None


class GuardRailsEngine:
    """Main guard rails orchestrator."""

    def __init__(self, config: dict = None):
        config = config or {}
        self.max_chars = config.get("max_chars", 500)
        self.approval_mode = config.get("approval_mode", False)
        self.approval_queue: list[dict] = []

        self.profanity = ProfanityFilter(config.get("profanity_words"))
        self.pii = PIIDetector()
        self.topics = TopicBlacklist(config.get("blacklisted_topics"))
        self.rate_limiter = RateLimiter(
            max_per_minute=config.get("rate_limit_per_minute", 10),
            per_chat_cooldown=config.get("rate_limit_cooldown", 10.0),
        )

    def process_incoming(self, chat_id: str, message: str) -> dict:
        """
        Check incoming message before AI processing.
        Returns: {"blocked": bool, "reason": str|None, "continue": bool}
        """
        # Rate limit checks
        reason = self.rate_limiter.check_global()
        if reason:
            return {"blocked": True, "reason": reason, "continue": False}

        reason = self.rate_limiter.check_chat(chat_id)
        if reason:
            return {"blocked": True, "reason": reason, "continue": False}

        # Length check
        if len(message) > self.max_chars:
            return {"blocked": True, "reason": f"Message too long ({len(message)} > {self.max_chars})", "continue": False}

        return {"blocked": False, "reason": None, "continue": True}

    def process_outgoing(self, chat_id: str, reply: str) -> dict:
        """
        Check AI-generated reply before sending.
        Returns: {"blocked": bool, "reason": str|None, "text": str}
        """
        # Profanity
        reason = self.profanity.is_blocked(reply)
        if reason:
            return {"blocked": True, "reason": reason, "text": reply}

        # PII
        reason = self.pii.has_pii(reply)
        if reason:
            return {"blocked": True, "reason": reason, "text": reply}

        # Blacklisted topics
        reason = self.topics.is_blocked(reply)
        if reason:
            return {"blocked": True, "reason": reason, "text": reply}

        # Length
        if len(reply) > self.max_chars:
            reply = reply[:self.max_chars] + "..."

        # Approval mode
        if self.approval_mode:
            entry = {"chat_id": chat_id, "reply": reply, "timestamp": time.time()}
            self.approval_queue.append(entry)
            return {"blocked": True, "reason": "Queued for human approval", "text": reply, "queued": True}

        return {"blocked": False, "reason": None, "text": reply}
