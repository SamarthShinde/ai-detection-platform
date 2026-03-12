# AI Detection Platform

A full-stack deepfake and AI-generated content detection platform built for **Apple M1** with GPU acceleration via Metal and MPS.

---

## Features

- **Multi-model ensemble** — Xception + EfficientNet for high accuracy detection
- **Video & image analysis** — frame-by-frame face detection with MediaPipe
- **REST API** — FastAPI with JWT authentication, rate limiting, API key management
- **Async processing** — Celery + Redis for non-blocking file processing
- **M1 optimized** — TensorFlow Metal + PyTorch MPS GPU acceleration
- **React frontend** — Upload, dashboard, results, and pricing pages

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| ML | TensorFlow-macos 2.14, PyTorch 2.1, OpenCV, MediaPipe |
| Database | PostgreSQL 14, Redis 7 |
| Async | Celery, Kombu |
| Frontend | React + Vite, Tailwind CSS, Recharts |
| Auth | JWT (python-jose), bcrypt |
| Testing | Pytest, pytest-asyncio, pytest-cov |

---

## Project Structure

```
ai-detection-platform/
├── backend/
│   └── app/
│       ├── models/        # SQLAlchemy database models
│       ├── routes/        # FastAPI route handlers
│       ├── schemas/       # Pydantic request/response schemas
│       ├── services/      # Business logic
│       └── utils/         # Helpers & dependencies
├── frontend/              # React + Vite app
│   ├── src/
│   │   ├── components/    # Auth, Upload, Results, Header
│   │   ├── pages/         # Dashboard, Pricing, Landing
│   │   └── contexts/      # Auth context & hooks
├── models/
│   └── pretrained/        # ML model weights (not committed)
├── datasets/
│   └── test_samples/      # Test images & videos
├── tests/                 # Pytest test suite
├── scripts/               # Benchmark & utility scripts
├── requirements.txt
└── docker-compose.yml
```

---

## Prerequisites

- macOS with Apple M1/M2/M3
- Homebrew
- Python 3.11 (via pyenv)
- Node.js 18+
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

### 3. Database

```bash
brew services start postgresql@14
brew services start redis
createdb ai_detection_dev
```

### 4. Environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Frontend

```bash
cd frontend
npm install
echo 'VITE_API_URL="http://localhost:8000"' > .env.local
```

---

## Running Locally

Open 3 terminals:

```bash
# Terminal 1 — Backend
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Celery worker
source venv/bin/activate
celery -A backend.app.tasks worker --loglevel=info

# Terminal 3 — Frontend
cd frontend
npm run dev
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Running with Docker

```bash
docker-compose up -d
```

---

## Testing

```bash
source venv/bin/activate
pytest tests/ -v --cov=backend.app --cov-report=html
```

---

## ML Models

The platform uses an ensemble of:

| Model | Framework | Accuracy | Input Size |
|---|---|---|---|
| Xception | PyTorch | 94% | 299×299 |
| EfficientNet-V2 | TensorFlow | 89% | 380×380 |

Models are loaded from `models/pretrained/` (not included in repo — see Day 8 setup guide).

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, get JWT token |
| GET | `/auth/me` | Get current user |
| POST | `/detections/video` | Upload video for detection |
| POST | `/detections/image` | Upload image for detection |
| GET | `/detections/{id}` | Get detection result |
| GET | `/detections` | List user's detections |
| POST | `/api-keys` | Create API key |
| GET | `/usage/stats` | Get usage statistics |

---

## Subscription Tiers

| Tier | Scans/month | Rate limit | Price |
|---|---|---|---|
| Free | 5 | 5 req/min | $0 |
| Pro | 100 | 50 req/min | $9.99/mo |
| Enterprise | Unlimited | Custom | Contact |

---

## Roadmap

- [x] M1 environment setup (Day 1-2)
- [ ] FastAPI backend (Day 3-7)
- [ ] ML detection engine (Day 8-11)
- [ ] React frontend (Day 12-15)
- [ ] Testing & Docker (Day 16-18)

---

## License

MIT
