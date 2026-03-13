# DeepDetect — AI Content Detection Platform

A production-ready full-stack platform for detecting AI-generated deepfakes in images and videos. Built for **Apple Silicon (M1/M2/M3)** with GPU acceleration via Metal/MPS.

---

## Live Demo (Local)

| Service | URL |
| --- | --- |
| Frontend | <http://localhost:5173> |
| Backend API | <http://localhost:8000> |
| Swagger Docs | <http://localhost:8000/docs> |

---

## Features

- **Real ML ensemble** — EfficientNet-B4 + Xception models running on MPS/CUDA/CPU with weighted voting
- **Image & video analysis** — frame-by-frame sampling for video, full preprocessing pipeline with ImageNet normalization
- **Email verification + 2FA** — 6-digit OTP via Gmail SMTP, Redis-backed with TTL, retry limits, and 60s resend cooldown
- **JWT authentication** — HS256 Bearer tokens, bcrypt (cost=12) passwords, inline 2FA challenge flow
- **Async processing** — Celery + Redis, solo pool (MPS-safe on Apple Silicon), 3× retry on failure
- **Smart caching** — SHA256 dedup skips re-processing identical files; DB-backed result cache
- **API key management** — `sk_live_` prefixed keys, SHA256-hashed in DB, constant-time verification
- **Rate limiting** — Redis-backed per-user per-minute/hour limits by subscription tier
- **Quota enforcement** — monthly scan limits with 429 responses when exceeded
- **React SPA** — Upload, Dashboard, Results, History, Batch, API Keys, Settings pages with dark UI

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI 0.109, Python 3.11, SQLAlchemy 2.0, Pydantic v2 |
| ML | PyTorch 2.1 (MPS), timm (EfficientNet-B4, Xception), torchvision, OpenCV |
| Database | PostgreSQL 14, Redis 7 |
| Async | Celery 5.3, solo pool (Apple Silicon safe) |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS v3, Zustand, Framer Motion |
| Auth | JWT (python-jose), bcrypt, email OTP, TOTP-style 2FA |
| Testing | Pytest, pytest-asyncio, pytest-cov |

---

## Project Structure

```text
ai-detection-platform/
├── backend/
│   └── app/
│       ├── ml/
│       │   ├── model_loader.py      # Thread-safe lazy model cache (MPS/CUDA/CPU)
│       │   ├── model_registry.py    # EfficientNet-B4 + Xception configs
│       │   ├── ensemble.py          # Weighted voting ensemble
│       │   ├── image_processor.py   # Image inference + artifact heuristics
│       │   ├── video_processor.py   # Frame sampling + aggregation
│       │   └── preprocessor.py      # ImageNet normalization transforms
│       ├── models/
│       │   └── database.py          # User, Detection, Batch, APIKey, UsageLog
│       ├── routes/
│       │   ├── auth.py              # Register, verify-email, login, 2FA, me, change-password, delete
│       │   ├── detection.py         # Upload image/video, poll, list, retry, delete
│       │   ├── api_keys.py          # Create, list (active+revoked), revoke
│       │   └── usage.py             # Usage stats and paginated history
│       ├── schemas/
│       │   ├── __init__.py          # UserResponse (with computed tier field), LoginRequest
│       │   ├── auth.py              # UpdateProfileRequest, ChangePasswordRequest
│       │   └── detection.py         # FileUploadResponse, DetectionStatusResponse
│       ├── services/
│       │   ├── auth_service.py      # JWT, bcrypt, user CRUD
│       │   ├── file_service.py      # Validation, SHA256 hashing, disk storage
│       │   ├── cache_service.py     # DB-backed result cache by file hash
│       │   ├── api_key_service.py   # Key generation, validation, revocation
│       │   ├── rate_limit_service.py # Redis atomic rate limiting per tier
│       │   └── usage_service.py     # Monthly quota tracking
│       ├── tasks/
│       │   ├── detection_tasks.py   # Celery async ML inference task (3x retry)
│       │   └── batch_tasks.py       # Batch progress aggregation
│       ├── middleware/
│       │   └── rate_limit_middleware.py  # Per-user rate limit middleware
│       ├── utils/
│       │   ├── config.py            # Pydantic Settings (reads .env)
│       │   ├── db.py                # SQLAlchemy engine + SessionLocal
│       │   ├── dependencies.py      # get_current_user, check_quota
│       │   ├── email_service.py     # Gmail SMTP via aiosmtplib
│       │   └── otp_service.py       # Redis OTP with TTL + cooldown
│       ├── celery_app.py            # Celery config, solo pool, task autodiscovery
│       └── main.py                  # FastAPI app, middleware, routers, model preload
├── frontend/
│   └── src/
│       ├── components/              # Layout, Toast, Badge, ProgressBar, LoadingStates
│       ├── pages/                   # Auth, Dashboard, Upload, Results, History, Batch, Settings
│       ├── hooks/                   # useAuth (login, register, verify2FA, refreshUser)
│       ├── store/                   # Zustand authStore + uiStore
│       └── utils/                   # api.ts (axios + interceptors), constants, validation
├── models/pretrained/               # ML weights (not committed — auto-downloaded via timm)
├── tests/                           # Pytest test suite
├── requirements.txt
└── .env                             # Environment variables (not committed)
```

---

## Prerequisites

- macOS with Apple M1/M2/M3 (or any Linux/Windows with CUDA/CPU)
- Python 3.11 (via pyenv recommended)
- Node.js 18+ and npm/pnpm
- PostgreSQL 14+
- Redis 7+

---

## Setup

### 1. Clone and enter the repo

```bash
git clone https://github.com/SamarthShinde/ai-detection-platform.git
cd ai-detection-platform
```

### 2. Python environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start services

```bash
brew services start postgresql@14
brew services start redis
createdb ai_detection_dev
```

### 4. Environment variables

Create `.env` in the project root:

```env
DATABASE_URL=postgresql://localhost/ai_detection_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-min-32-chars-here
ENVIRONMENT=development
LOG_LEVEL=INFO

# Email / OTP (Gmail — create an App Password in Google Account settings)
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

### 6. Frontend dependencies

```bash
cd frontend
npm install
```

---

## Running Locally

Open **3 terminals** from the project root:

```bash
# Terminal 1 — Backend API
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker (solo pool — MPS safe on Apple Silicon)
cd backend
source ../venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 3 — Frontend
cd frontend
npm run dev
```

> ML model weights (~200 MB) are downloaded automatically from HuggingFace on first worker start.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/auth/register` | Register; triggers email OTP |
| POST | `/auth/verify-email` | Submit OTP to activate account |
| POST | `/auth/resend-otp` | Resend OTP (60s cooldown) |
| POST | `/auth/login` | Login; returns JWT or 2FA challenge |
| POST | `/auth/verify-2fa` | Submit 2FA OTP, receive full JWT |
| POST | `/auth/toggle-2fa` | Enable/disable email 2FA |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user profile |
| PUT | `/auth/me` | Update display name |
| POST | `/auth/change-password` | Change password (requires current password) |
| DELETE | `/auth/me` | Permanently delete account |
| POST | `/auth/logout` | Logout (client-side token discard) |

### Detection

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/detections/image` | Upload image (jpg/png/webp <=10 MB); returns 202 |
| POST | `/detections/video` | Upload video (mp4/avi/mov/mkv <=100 MB); returns 202 |
| GET | `/detections/{id}` | Poll status + results |
| GET | `/detections` | List detections (paginated) |
| POST | `/detections/{id}/retry` | Retry a failed detection |
| DELETE | `/detections/{id}` | Delete detection record |

### API Keys

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api-keys` | Create key (shown once in full) |
| GET | `/api-keys` | List all keys with masked previews |
| DELETE | `/api-keys/{id}` | Revoke a key |
| DELETE | `/api-keys` | Revoke all keys |

### Usage & Quota

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/usage/stats` | Scans used, limit, API calls, renewal date |
| GET | `/usage/history` | Paginated request log |

---

## Authentication Flow

```text
Register → Email OTP → Verify → Login → (2FA OTP if enabled) → JWT Bearer token
```

- Passwords: 8+ chars, uppercase, lowercase, digit, special character
- OTP: 6-digit, 15-min TTL, max 3 attempts, 60s resend cooldown
- JWT: HS256, Bearer token in `Authorization` header
- API keys: `sk_live_` prefix, SHA256-hashed in DB, constant-time comparison

---

## Detection Flow

```text
Upload → SHA256 hash → Cache check → Duplicate check → Save to disk
→ Create Detection record (status=pending) → Dispatch Celery task → Return 202

Celery worker:
  → Load EfficientNet-B4 + Xception (lazy, cached after first load)
  → Preprocess (resize, ImageNet normalize)
  → Weighted ensemble inference (MPS GPU on Apple Silicon)
  → Persist results → status=completed
  → Cache result by file hash (skips ML on re-upload of identical file)
```

**Result fields:**

- `ai_probability` — 0.0–1.0 likelihood of AI generation
- `confidence_score` — inter-model agreement (0=disagreement, 1=full agreement)
- `detection_methods` — `"efficientnet_b4:0.xx;xception:0.xx"` per-model scores
- `processing_time_ms` — end-to-end processing time

---

## Subscription Tiers

| Tier | Scans/month | Requests/min | Requests/hour |
| --- | --- | --- | --- |
| Free | 10 | 60 | 1,000 |
| Pro | 500 | 120 | 5,000 |
| Enterprise | Unlimited | Unlimited | Unlimited |

---

## Known Issues & Architecture Notes

- **Apple Silicon (MPS):** Celery uses `worker_pool=solo` to prevent SIGABRT from MPS Metal compiler being non-fork-safe in child processes. Tasks run sequentially — acceptable for V0/demo, upgrade to `gevent` pool for production.
- **Model accuracy:** Models use ImageNet-pretrained backbones (EfficientNet-B4, Xception) with a single-class head. For production deepfake detection, fine-tune on [FaceForensics++](https://github.com/ondyari/FaceForensics) or similar datasets.
- **Model weights:** Downloaded automatically via `timm` from HuggingFace on first worker start (~200 MB). Cached in `~/.cache/huggingface/hub/`.

---

## Roadmap

- [x] Day 1-2: M1 environment, PostgreSQL, Redis, ML stack, React scaffold
- [x] Day 3: FastAPI, SQLAlchemy models, JWT auth (register/login/me)
- [x] Day 4: Auth routes, Pydantic v2 schemas, CORS, middleware
- [x] Day 4.5: Email verification (OTP), 2FA, Gmail SMTP, Redis TTL
- [x] Day 5: File upload, SHA256 dedup, Celery async pipeline, detection polling
- [x] Day 6: API key management, usage tracking, quota enforcement
- [x] Day 7: Rate limiting middleware, API key validation flow
- [x] Day 8-11: ML ensemble (EfficientNet-B4, Xception), MPS inference, result caching
- [x] Day 12-15: Full React frontend (Auth, Dashboard, Upload, Results, History, Batch, Settings)
- [x] QA pass: 2FA inline flow, quota display, blob URL cleanup, SPA navigation, 401 interceptor, account deletion, profile/password endpoints, rate limit tuning, Celery MPS fix
- [ ] Fine-tune models on deepfake dataset (FaceForensics++)
- [ ] Docker Compose setup
- [ ] Production deployment (fly.io / Railway)

---

## Testing

```bash
source venv/bin/activate
pytest tests/ -v --cov=backend/app --cov-report=html
```

---

## License

MIT
