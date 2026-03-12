# AI Detection Platform

A full-stack deepfake and AI-generated content detection platform built for **Apple M1** with GPU acceleration via Metal and MPS.

---

## Features

- **Multi-model ensemble** — Xception + EfficientNet for high accuracy detection (Day 8-11)
- **Video & image analysis** — frame-by-frame face detection with MediaPipe
- **REST API** — FastAPI with JWT authentication, rate limiting, API key management
- **Email verification + 2FA** — OTP via Gmail SMTP, Redis-backed with TTL and retry limits
- **Async processing** — Celery + Redis for non-blocking file processing
- **Quota enforcement** — per-tier monthly scan limits with 429 responses
- **M1 optimized** — TensorFlow Metal + PyTorch MPS GPU acceleration
- **React frontend** — Upload, dashboard, results, and pricing pages (Day 12-15)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| ML | TensorFlow-macos 2.14, PyTorch 2.1, OpenCV, MediaPipe |
| Database | PostgreSQL 14, Redis 7 |
| Async | Celery, Kombu |
| Frontend | React + Vite, Tailwind CSS v3, Recharts |
| Auth | JWT (python-jose), bcrypt (cost=12), email OTP, 2FA |
| Testing | Pytest, pytest-asyncio, pytest-cov |

---

## Project Structure

```
ai-detection-platform/
├── backend/
│   └── app/
│       ├── models/
│       │   └── database.py        # User, Detection, APIKey, UsageLog models
│       ├── routes/
│       │   ├── auth.py            # Register, login, verify-email, 2FA, me
│       │   ├── detection.py       # Upload video/image, poll status, list, delete
│       │   ├── api_keys.py        # Create, list, revoke API keys
│       │   └── usage.py           # Usage stats and history
│       ├── schemas/
│       │   ├── auth.py            # RegisterRequest, LoginRequest, TokenResponse, etc.
│       │   └── detection.py       # FileUploadResponse, DetectionStatusResponse, etc.
│       ├── services/
│       │   ├── auth_service.py    # JWT, bcrypt, user CRUD
│       │   ├── file_service.py    # Validation, SHA256 hashing, disk storage
│       │   ├── api_key_service.py # Key generation, validation, revocation
│       │   └── usage_service.py   # Monthly quota tracking and enforcement
│       ├── tasks/
│       │   └── detection_tasks.py # Celery async detection task
│       ├── utils/
│       │   ├── config.py          # Pydantic Settings (reads .env)
│       │   ├── db.py              # SQLAlchemy engine + SessionLocal
│       │   ├── dependencies.py    # get_current_user, check_quota
│       │   ├── api_key_utils.py   # Key generation + SHA256 hashing
│       │   ├── email_service.py   # Gmail SMTP via aiosmtplib
│       │   └── otp_service.py     # Redis-backed OTP with TTL + cooldown
│       ├── celery_app.py          # Celery config + task autodiscovery
│       └── main.py                # FastAPI app, middleware, routers
├── frontend/                      # React + Vite app (scaffold complete)
│   └── src/
│       ├── components/
│       ├── pages/
│       └── contexts/
├── models/
│   └── pretrained/                # ML model weights (not committed)
├── datasets/
│   └── test_samples/              # Test images & videos
├── tests/                         # Pytest test suite
├── uploads/                       # Uploaded files (not committed)
├── requirements.txt
└── .env                           # Environment variables (not committed)
```

---

## Prerequisites

- macOS with Apple M1/M2/M3
- Homebrew
- Python 3.11 (via pyenv)
- Node.js 18+ and pnpm
- PostgreSQL 14+
- Redis 7+

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/SamarthShinde/ai-detection-platform.git
cd ai-detection-platform
```

### 2. Python environment

```bash
pyenv install 3.11.0
pyenv local 3.11.0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Database and cache

```bash
brew services start postgresql@14
brew services start redis
createdb ai_detection_dev
```

### 4. Environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://localhost/ai_detection_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-min-32-chars
ENVIRONMENT=development
LOG_LEVEL=INFO

# Email / OTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-gmail@gmail.com
OTP_EXPIRY_MINUTES=15
ENABLE_EMAIL_2FA=true

# CORS
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### 5. Initialize the database

```bash
cd backend
source ../venv/bin/activate
python init_db.py
```

### 6. Frontend

```bash
cd frontend
pnpm install
echo 'VITE_API_URL="http://localhost:8000"' > .env.local
```

---

## Running Locally

Open 3 terminals from the project root:

```bash
# Terminal 1 — Backend API
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker
cd backend
source ../venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 3 — Frontend
cd frontend
pnpm dev
```

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register; triggers email OTP verification |
| POST | `/auth/verify-email` | Verify OTP to activate account |
| POST | `/auth/resend-otp` | Resend verification OTP (60s cooldown) |
| POST | `/auth/login` | Login; returns JWT or triggers 2FA flow |
| POST | `/auth/verify-2fa` | Submit 2FA OTP to get full JWT |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user profile |
| POST | `/auth/logout` | Logout (client-side token discard) |
| POST | `/auth/toggle-2fa` | Enable or disable email 2FA |

### Detection

| Method | Endpoint | Description |
|---|---|---|
| POST | `/detections/video` | Upload video (mp4/avi/mov/mkv, ≤100 MB); returns 202 |
| POST | `/detections/image` | Upload image (jpg/png/webp, ≤10 MB); returns 202 |
| GET | `/detections/{id}` | Poll for status and results |
| GET | `/detections` | List detections (paginated) |
| DELETE | `/detections/{id}` | Delete detection and uploaded file |

### API Keys

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api-keys` | Create API key (full key shown once only) |
| GET | `/api-keys` | List active keys (masked previews) |
| DELETE | `/api-keys/{id}` | Revoke an API key |

### Usage & Quota

| Method | Endpoint | Description |
|---|---|---|
| GET | `/usage/stats` | Current month scan count, limit, renewal date |
| GET | `/usage/history` | Paginated request log (query: skip, limit, days) |

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/docs` | Swagger UI |

---

## Authentication Flow

```
Register → Email OTP → Verify → Login → (2FA OTP if enabled) → JWT
```

- Passwords require: 8+ chars, uppercase, lowercase, digit, special char
- OTP: 6-digit, 15-min TTL, max 3 attempts, 60s resend cooldown
- JWT: HS256, configurable expiry, Bearer token auth
- API keys: SHA256-hashed in DB, `sk_live_` prefix, constant-time verify

---

## Detection Flow

```
Upload file → SHA256 hash → Duplicate check → Save to disk
→ Create Detection record → Submit Celery task → Return 202
→ Poll /detections/{id} → pending → processing → completed
```

**Detection result fields:**
- `ai_probability` — 0.0–1.0 likelihood of AI generation
- `confidence_score` — model confidence in the result
- `detection_methods` — comma-separated method:score pairs
- `processing_time_ms` — end-to-end processing time

> Note: ML inference is currently a stub (returns fixed values). Real ensemble (XceptionNet + EfficientNet) integrates on Day 8-11.

---

## Subscription Tiers & Quotas

| Tier | Scans/month | Requests/min | Price |
|---|---|---|---|
| Free | 5 | 2 | $0 |
| Pro | 100 | 30 | $9.99/mo |
| Enterprise | Unlimited | Unlimited | Contact |

Exceeding the monthly scan limit returns `429 Too Many Requests`.

---

## Database Models

| Model | Key Fields |
|---|---|
| `User` | email, password_hash, subscription_tier, is_verified, email_2fa_enabled |
| `Detection` | user_id, file_hash, file_type, processing_status, ai_probability, confidence_score |
| `APIKey` | user_id, key_hash, name, active, last_used |
| `UsageLog` | user_id, endpoint, timestamp, file_size_bytes, processing_time_ms, status_code |

---

## ML Models (Day 8-11)

The platform uses an ensemble of:

| Model | Framework | Target Accuracy | Input Size |
|---|---|---|---|
| Xception | PyTorch | ~94% | 299×299 |
| EfficientNet-V2 | TensorFlow | ~89% | 380×380 |

Models will be loaded from `models/pretrained/` (not included in repo).

---

## Roadmap

- [x] Day 1-2: M1 environment, pyenv, PostgreSQL, Redis, ML stack, React scaffold
- [x] Day 3: FastAPI app, SQLAlchemy models, JWT auth (register/login/me)
- [x] Day 4: Auth routes (refresh, logout), Pydantic schemas, CORS, middleware
- [x] Day 4.5: Email verification (OTP), 2FA (email OTP), Gmail SMTP, Redis TTL
- [x] Day 5: File upload (video + image), SHA256 dedup, Celery async pipeline, detection polling
- [x] Day 6: API key management (create/list/revoke), usage tracking, quota enforcement per tier
- [ ] Day 7: Rate limiting middleware, additional API management
- [ ] Day 8-11: ML detection engine (XceptionNet, EfficientNet, MediaPipe faces)
- [ ] Day 12-15: React frontend (upload UI, dashboard, results, pricing)
- [ ] Day 16-18: Testing, Docker, deployment

---

## Testing

```bash
source venv/bin/activate
pytest tests/ -v --cov=backend.app --cov-report=html
```

---

## License

MIT
