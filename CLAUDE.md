# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Assistant Pronote IA is a web application that provides access to Pronote (French school management system) with CAS authentication support for regional ENTs, integrated with an AI conversational assistant powered by OpenRouter.

**Architecture:**
- Backend: Python FastAPI with pronotepy library for Pronote access
- Frontend: Vanilla JavaScript (HTML/CSS/JS) - deployable to GitHub Pages
- Session Management: Redis with encrypted credentials (AES-256-GCM)
- Authentication: JWT tokens + Redis sessions
- AI Integration: OpenRouter API (DeepSeek R1)

## Development Commands

### Backend Development

```bash
# Setup environment
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start Redis (required)
redis-server

# Run development server
python server.py
# Backend runs on http://localhost:8000
# API docs: http://localhost:8000/docs (only in DEBUG mode)
```

### Frontend Development

```bash
cd frontend

# Simple HTTP server
python -m http.server 3000
# OR
npx http-server -p 3000

# Frontend runs on http://localhost:3000
```

### Docker Development

```bash
# Start all services (backend, frontend, Redis, Redis Commander)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Testing Backend

```bash
# Health check
curl http://localhost:8000/api/health

# List supported ENTs
curl http://localhost:8000/api/ents

# Test authentication (direct)
curl -X POST http://localhost:8000/api/auth/login/direct \
  -H "Content-Type: application/json" \
  -d '{"pronote_url":"https://...", "username":"...", "password":"..."}'
```

## Architecture Details

### Authentication Flow

1. **Login** (`/api/auth/login/direct` or `/api/auth/login/cas`)
   - User submits credentials
   - Backend authenticates with Pronote via `pronotepy`
   - Credentials are encrypted with Fernet (AES-256-GCM)
   - Session data stored in Redis with TTL
   - JWT token generated containing `session_token` reference
   - Frontend stores JWT in `sessionStorage`

2. **Authenticated Requests**
   - Frontend sends JWT in `Authorization: Bearer <token>` header
   - `get_current_user` dependency validates JWT
   - Session data retrieved from Redis using `session_token` from JWT
   - Credentials decrypted for Pronote re-authentication (pronotepy limitation)

3. **Session Lifecycle**
   - JWT expires after `JWT_EXPIRATION_HOURS` (default: 24h)
   - Redis session expires after `SESSION_EXPIRATION_SECONDS` (default: 24h)
   - Activity updates refresh Redis TTL
   - Logout deletes Redis session

### Pronotepy Integration Pattern

**Critical Limitation:** pronotepy does not support session persistence - you must re-authenticate for each Pronote data fetch.

**Current Implementation:**
```python
# In /api/pronote/homework, /api/pronote/timetable, /api/pronote/grades
client = PronoteClient()
# Re-authenticate using stored credentials (encrypted in Redis)
if pronote_data['auth_type'] == 'direct':
    await client.authenticate_direct(...)
else:
    await client.authenticate_cas(...)
# Then fetch data
homework = await client.get_homework(...)
```

**Why:** pronotepy `Client` objects cannot be serialized/deserialized, so we store credentials and recreate sessions.

### Redis Data Structure

```
session:{session_token} → {
  "user_id": "username_sessionid",
  "pronote_data": "<encrypted_json>",  # Contains credentials, session_info
  "created_at": "ISO8601",
  "last_activity": "ISO8601"
}
```

Encrypted `pronote_data` contains:
- `pronote_url`
- `username`
- `password` (encrypted)
- `ent_name` (if CAS)
- `session_info` (student name, class, establishment)
- `auth_type` ("direct" or "cas")

### Frontend-Backend Communication

**Frontend Architecture:**
- `config.js`: Configuration (API_BASE_URL, AI_CONFIG)
- `api-client.js`: APIClient class handles all HTTP requests, token management
- `auth.js`: Authentication UI and flows
- `pronote-data.js`: Fetches homework/timetable/grades
- `chat.js`: AI chat interface
- `app.js`: Main initialization and routing

**API Endpoints:**
- `POST /api/auth/login/direct` - Direct Pronote auth
- `POST /api/auth/login/cas` - CAS auth (27+ ENTs supported)
- `POST /api/auth/logout` - Destroy session
- `POST /api/pronote/homework` - Get homework (date_from, date_to)
- `POST /api/pronote/timetable` - Get schedule
- `POST /api/pronote/grades` - Get grades (optional period_name)
- `POST /api/ai/chat` - Chat with AI (message, context, model)
- `GET /api/ents` - List supported ENTs
- `GET /api/health` - Health check

### CAS Authentication Support

27+ French regional ENTs supported via pronotepy's `ent_list`:
- Île-de-France: monlycee.net, Paris Classe Numérique, ENT77, ENT94
- Grand Est: Mon Bureau Numérique
- Nouvelle-Aquitaine: Lycée Connecté
- Occitanie: Néo
- Bretagne: Toutatice
- And more...

**Implementation:** See `pronote_client.py::authenticate_cas()` and `SUPPORTED_ENTS` list.

### Environment Variables (Backend)

**Required for Production:**
```bash
SECRET_KEY=<32+ char random string>
JWT_SECRET_KEY=<32+ char random string>
ENCRYPTION_KEY=<32+ char random string>
OPENROUTER_API_KEY=<your openrouter key>
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

**Optional:**
```bash
PORT=8000
DEBUG=False
SESSION_EXPIRATION_SECONDS=86400
JWT_EXPIRATION_HOURS=24
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
LOG_LEVEL=INFO
```

Generate secrets:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Frontend Configuration

**Edit `frontend/js/config.js` for production:**
```javascript
const CONFIG = {
    API_BASE_URL: 'https://your-backend.railway.app',  // Change for production
    DEBUG: false  // Disable in production
};
```

## Deployment

### Backend: Railway.app

1. Create Railway account, link GitHub repo
2. Add Redis database to project
3. Configure environment variables (see above)
4. Railway auto-deploys from `backend/` with Dockerfile
5. Health check: `https://your-app.railway.app/api/health`

### Frontend: GitHub Pages

1. Push `frontend/` directory to GitHub repo
2. Enable GitHub Pages from Settings → Pages
3. Deploy from branch `main`, folder `/(root)`
4. Update `frontend/js/config.js` with Railway backend URL
5. Update Railway `ALLOWED_ORIGINS` with GitHub Pages URL

### Docker Production

```bash
# Build backend
docker build -t pronote-backend ./backend

# Run with env file
docker run -p 8000:8000 --env-file .env pronote-backend
```

See `docs/DEPLOIEMENT.md` for detailed deployment instructions.

## Key Dependencies

**Backend:**
- `fastapi`: Web framework
- `pronotepy==2.12.0`: Pronote API with CAS support
- `redis`: Session storage
- `cryptography`: Fernet encryption for credentials
- `pyjwt`: JWT token generation/validation
- `httpx`: Async HTTP client for OpenRouter
- `slowapi`: Rate limiting
- `loguru`: Logging
- `pydantic-settings`: Environment variable management

**Frontend:**
- Vanilla JavaScript (no build step required)
- No npm dependencies

## Common Issues and Solutions

### 1. Password Storage Pattern

**Problem:** pronotepy requires re-authentication for each request.

**Solution:** Store encrypted credentials in Redis, decrypt only when needed for pronotepy authentication. Never log decrypted passwords.

### 2. CORS Errors

Ensure `ALLOWED_ORIGINS` in backend `.env` matches frontend URL exactly:
```bash
# Development
ALLOWED_ORIGINS=http://localhost:3000

# Production
ALLOWED_ORIGINS=https://username.github.io
```

### 3. Redis Connection

Backend requires Redis to be running. Check connection:
```bash
redis-cli ping  # Should return PONG
```

In Docker: `docker-compose ps` should show redis as "Up".

### 4. Rate Limiting

FastAPI uses `slowapi` with decorators:
```python
@app.post("/api/auth/login/direct")
@limiter.limit("10/minute")  # Max 10 requests per minute
```

Limits are per IP address. Adjust in `config.py` if needed.

### 5. OpenRouter API Key

Free tier supports DeepSeek R1 model. Get key at https://openrouter.ai/keys.

**Never commit API keys.** Use environment variables only.

## Security Notes

- All credentials encrypted at rest (AES-256-GCM via Fernet)
- JWT tokens with expiration
- Rate limiting on all endpoints
- CORS restricted to allowed origins
- HTTPS enforced in production (Railway/GitHub Pages)
- No credentials in logs (loguru filters passwords)
- Session data stored server-side only

## Code Style

- Python: Follow PEP 8, use type hints where possible
- JavaScript: ES6+, use `const`/`let`, async/await
- Error handling: Use custom exceptions (`PronoteException`, `CASAuthenticationError`)
- Logging: Use `loguru` for backend, `debugLog`/`errorLog` for frontend
- Comments: Docstrings for all functions, inline comments for complex logic

## Monitoring and Debugging

**Backend Logs:**
```bash
# View logs
tail -f backend/logs/app.log

# Docker
docker-compose logs -f backend
```

**Redis Debugging:**
```bash
# Connect to Redis CLI
redis-cli

# View session
GET "session:your-token-here"

# List all sessions
KEYS "session:*"
```

**Frontend Debugging:**
- Open browser DevTools (F12)
- Check Console for `[DEBUG]` and `[ERROR]` logs
- Network tab: inspect API requests/responses
- Application tab: check sessionStorage for `access_token`

## Important Files

- `backend/server.py`: FastAPI main application, all endpoints
- `backend/auth.py`: SessionManager, JWTManager, AuthenticationService
- `backend/pronote_client.py`: PronoteClient with CAS support, retry logic
- `backend/config.py`: Settings with pydantic validation
- `frontend/js/api-client.js`: APIClient class for all HTTP requests
- `frontend/js/config.js`: Frontend configuration (must edit for production)
- `docker-compose.yml`: Development environment with all services
- `railway.toml`: Railway deployment configuration

## Troubleshooting Commands

```bash
# Test backend health
curl http://localhost:8000/api/health

# Test Redis connection
redis-cli ping

# View backend logs
docker-compose logs backend

# Restart services
docker-compose restart

# Check ENT support
curl http://localhost:8000/api/ents

# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
