# WhatsApp AI Auto-Reply 🤖💬

Production-ready AI-powered auto-reply system for WhatsApp with guard rails, built using WAHA, FastAPI, and local/cloud LLMs.

---

## Architecture

```
WhatsApp → WAHA (HTTP API) → Webhook → AI Microservice (FastAPI) → Guard Rails → Ollama/OpenAI → Reply
```

**Components:**
- **WAHA** - WhatsApp HTTP API (connects to WhatsApp Web, provides webhooks)
- **AI Microservice** - FastAPI app that processes messages through guard rails and AI
- **Guard Rails Engine** - Profanity filter, PII detection, topic blacklist, rate limiting
- **Ollama / OpenAI** - AI reply generation (local or cloud)

---

## Quick Start

```bash
git clone https://github.com/kanna-sakthi27/whatsapp-ai-autoreply.git
cd whatsapp-ai-autoreply
chmod +x setup.sh
./setup.sh
# Edit .env with your settings
nano .env
# Start services
docker compose up -d
# Scan WhatsApp QR code
docker logs waha-whatsapp -f
```

---

## Features

| Feature | Details |
|---------|---------|
| AI Replies | Local (Ollama) or Cloud (OpenAI) LLM integration |
| Guard Rails | Profanity filter, PII detection, topic blacklist, rate limiting |
| Approval Mode | Queue AI replies for human review before sending |
| One-Command Deploy | Single `docker compose up -d` |
| Webhooks | Event-driven architecture, no browser automation |
| Multi-Session | Support for multiple WhatsApp accounts |

---

## Guard Rails

Two-phase filtering:
1. **Incoming Check** - Rate limit, message length before AI processing
2. **Outgoing Check** - Profanity, PII, blacklisted topics before sending

| Guard | Catches |
|-------|--------|
| Profanity Filter | Spam phrases, scams |
| PII Detection | Emails, phones, SSNs, credit cards, IPs |
| Topic Blacklist | Politics, illegal, weapons, drugs |
| Rate Limiter | 10/min global, 10s per-chat cooldown |
| Length Limiter | Max 500 chars per message |
| Approval Mode | Queue all replies for human review |

---

## Tech Stack & Credits

This project uses the following amazing open-source tools:

| Project | Role | Link |
|---------|------|------|
| **WAHA** | WhatsApp HTTP API (production backbone) | https://waha.devlike.pro/ |
| **Ollama** | Local LLM inference | https://ollama.ai |
| **OpenAI** | Cloud LLM API | https://openai.com |
| **FastAPI** | Python web framework | https://fastapi.tiangolo.com |
| **Agent Zero** | AI agent framework that built this project | https://github.com/frdel/agent-zero |
| **OpenWA** | Reference WhatsApp API architecture | https://github.com/rmyndharis/OpenWA |
| **Docker Compose** | Container orchestration | https://docs.docker.com/compose/ |

> **Why WAHA over Playwright?** WAHA is a dedicated WhatsApp HTTP API without browser automation, providing stable webhooks, session persistence, and production-grade reliability.

---

## Project Structure

```
whatsapp-ai-autoreply/
├── ai_service/
│   ├── Dockerfile          # Container build
│   ├── main.py             # FastAPI application
│   ├── guard_rails.py      # Guard rails engine
│   └── requirements.txt    # Python dependencies
├── docker-compose.yml      # Service orchestration
├── .env.example            # Environment template
├── setup.sh                # One-time setup script
├── README.md               # This file
├── waha_sessions/          # WAHA session data (gitignored)
├── waha_media/             # WAHA media files (gitignored)
└── ollama_data/            # Ollama model data (gitignored)
```

---

## Configuration

Edit `.env` file (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | ollama | `ollama` or `openai` |
| `OLLAMA_BASE_URL` | http://host.docker.internal:11434 | Ollama server |
| `OLLAMA_MODEL` | llama3.2:1b | Ollama model |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | gpt-4o-mini | OpenAI model |
| `MAX_CHARS` | 500 | Max message length |
| `RATE_LIMIT_PER_MINUTE` | 10 | Global rate limit |
| `APPROVAL_MODE` | false | Queue for human review |

---

## API Endpoints (AI Service - port 8000)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/webhook/message` | Process incoming message |
| POST | `/webhook/message/raw` | Raw WAHA webhook |
| POST | `/send` | Manually send message |
| GET | `/guard-queue` | Pending approvals |
| POST | `/guard-queue/approve` | Approve queued item |

---


## Frontend Dashboard

The project now includes a modern React dashboard (Vite + MUI) with a dark Grafana/Datadog-style theme for managing your WhatsApp AI auto-reply system.

### Access

The dashboard is served on **port 8080** when running `docker-compose up -d`.

### Features
- **Dashboard**: Stats overview (messages today, blocked, AI replies, approval queue, active conversations, uptime)
- **Messages**: Message history table with conversation view
- **Send Message**: Send WhatsApp messages directly from the browser
- **Approval Queue**: Review and approve/block messages held by guard rails
- **AI Provider Config**: Switch between Ollama, OpenAI, Anthropic, Google, Groq, and more
- **Guard Rails Config**: Toggle profanity filter, PII detection, topic blacklist, rate limiting, approval mode
- **General Settings**: Configure WAHA base URL, max conversation history, default language, log level
- **Log Viewer**: Searchable, filterable log viewer with auto-refresh and expandable details
- **Connection Status**: WAHA connection health monitoring

### Development

```bash
cd frontend
npm install
npm run dev  # Runs on port 5173 with hot reload, proxied to backend
npm run build  # Production build to dist/
```

### Architecture

The frontend is served by Nginx inside the Docker container and proxies:
- `/api/*` → `ai-service:8000`
- `/waha/*` → `waha:3000`

All API requests from the browser go through the same domain (port 8080), avoiding CORS issues.

## License

MIT License

---

<div align="center">
  Built with ❤️ using <a href="https://github.com/frdel/agent-zero">Agent Zero</a><br>
  GitHub: <a href="https://github.com/kanna-sakthi27">kanna-sakthi27</a>
</div>
