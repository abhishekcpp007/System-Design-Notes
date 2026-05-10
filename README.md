# Portfolio Website — Full-Stack Production-Grade Application

> A complete portfolio website built with enterprise architecture patterns used at Google, Netflix, and Stripe. Backend in FastAPI (Python), Frontend in Next.js 14 (TypeScript).

---

## Quick Start (2 Minutes)

### Prerequisites

Make sure you have these installed:

| Tool | Version | Check Command | Install |
|------|---------|---------------|---------|
| Python | 3.11+ | `python --version` | [python.org](https://python.org) |
| Node.js | 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| Docker | 24+ | `docker --version` | [docker.com](https://docker.com) (optional but recommended) |
| Git | Any | `git --version` | [git-scm.com](https://git-scm.com) |

### Step 1: Run Setup Script

```bash
# Clone/navigate to the project
cd Portfolio

# Run the interactive setup (fills all config automatically)
./setup.sh
```

The script will ask you for:

| Data Required | Where to Get It | Required? |
|---------------|----------------|-----------|
| Your Name | — | Yes |
| Your Email | — | Yes |
| GitHub Username | Your GitHub profile | Yes |
| Domain | Your custom domain (skip for localhost) | No |
| Database | Local Docker or Supabase URL | Yes |
| Redis | Local Docker or Upstash URL | Yes |
| GitHub Token | GitHub → Settings → Developer settings → Tokens | No (recommended) |
| GitHub OAuth | GitHub → Settings → Developer settings → OAuth Apps | No |
| Google OAuth | Google Cloud Console → Credentials | No |
| SMTP Email | Gmail App Password or any SMTP | No |
| Sentry DSN | sentry.io dashboard | No |

### Step 2: Run the Project

You have two options:

---

## Option A: Run with Docker (Easiest — Recommended)

```bash
# Start everything (backend + frontend + database + redis)
docker-compose up -d

# Wait 30 seconds for everything to start, then open:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs

# To stop everything:
docker-compose down

# To see logs:
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Option B: Run Without Docker (Manual Setup)

### Terminal 1: Start Database & Redis

```bash
# If using local PostgreSQL and Redis (via Docker just for DB):
docker run -d --name portfolio-db -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=portfolio \
  postgres:16-alpine

docker run -d --name portfolio-redis -p 6379:6379 redis:7-alpine

# OR if using Supabase + Upstash: skip this step (cloud databases)
```

### Terminal 2: Start Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows CMD
# venv\Scripts\Activate.ps1    # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Run database migrations (creates all tables)
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Terminal 3: Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

You should see:
```
▲ Next.js 14.2.x
- Local:   http://localhost:3000
- Ready in 2.5s
```

### Open in Browser

| URL | What |
|-----|------|
| http://localhost:3000 | Your portfolio website |
| http://localhost:8000 | Backend API root |
| http://localhost:8000/docs | Swagger API Documentation (Interactive!) |
| http://localhost:8000/redoc | ReDoc API Documentation (Beautiful!) |
| http://localhost:8000/health | Health check endpoint |

---

## Create Your Admin Account

After the project is running, create your admin account:

```bash
# Using curl (Mac/Linux):
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "password": "YourSecurePassword123!",
    "full_name": "Your Name"
  }'

# OR use the Swagger UI:
# 1. Go to http://localhost:8000/docs
# 2. Find POST /api/v1/auth/signup
# 3. Click "Try it out"
# 4. Fill in the details and execute
```

Then to make yourself admin, run this SQL (via Supabase dashboard or psql):

```sql
UPDATE users SET role = 'admin' WHERE email = 'your-email@gmail.com';
```

Now login at http://localhost:3000/auth/login and you'll have full admin access!

---

## Project Structure

```
Portfolio/
├── setup.sh                    ← Run this first! Interactive setup wizard
├── docker-compose.yml          ← Docker services (one command to run all)
├── .gitignore                  ← Files that should NOT go to GitHub
├── PORTFOLIO_BOOK.md           ← 29-chapter technical book explaining everything
├── DEPLOYMENT.md               ← Step-by-step deployment guide
├── README.md                   ← This file
│
├── backend/                    ← FastAPI Python Backend
│   ├── app/
│   │   ├── main.py            ← Entry point
│   │   ├── config.py          ← Environment settings
│   │   ├── database.py        ← DB connection
│   │   ├── models/            ← Database tables (SQLAlchemy)
│   │   ├── schemas/           ← Request/Response validation (Pydantic)
│   │   ├── api/v1/            ← All API routes/controllers
│   │   ├── services/          ← Business logic, email, GitHub, cache
│   │   ├── middleware/        ← Rate limiting, security headers, CORS
│   │   └── utils/             ← Helpers (JWT, validation, exceptions)
│   ├── alembic/               ← Database migrations
│   ├── tests/                 ← 55+ test cases
│   ├── requirements.txt       ← Python dependencies
│   ├── Dockerfile             ← Container config
│   ├── .env                   ← Your local config (created by setup.sh)
│   └── .env.example           ← Template showing what's needed
│
├── frontend/                   ← Next.js 14 TypeScript Frontend
│   ├── src/
│   │   ├── app/               ← Pages (Next.js App Router)
│   │   │   ├── page.tsx       ← Home page
│   │   │   ├── projects/      ← Projects listing + detail
│   │   │   ├── blog/          ← Blog listing + detail
│   │   │   ├── contact/       ← Contact form
│   │   │   ├── auth/          ← Login page
│   │   │   └── admin/         ← Admin dashboard
│   │   ├── components/        ← Reusable UI components
│   │   │   ├── layout/        ← Navbar, Footer
│   │   │   ├── sections/      ← Hero, Features
│   │   │   └── ui/            ← Error boundary, accessibility
│   │   ├── lib/               ← Utilities, API client, store
│   │   ├── hooks/             ← Custom React hooks
│   │   ├── types/             ← TypeScript interfaces
│   │   └── styles/            ← Global CSS
│   ├── public/                ← Static files, PWA manifest, service worker
│   ├── e2e/                   ← Playwright end-to-end tests
│   ├── package.json           ← Node dependencies
│   ├── Dockerfile             ← Container config
│   └── .env.local             ← Your local config (created by setup.sh)
│
└── .github/
    └── workflows/
        └── ci.yml             ← GitHub Actions CI/CD pipeline
```

---

## Available Commands

### Backend Commands

```bash
cd backend
source venv/bin/activate

# Run server (development with auto-reload)
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=html

# Run linter
ruff check .

# Run formatter
black .

# Run type checker
mypy app/

# Create new database migration
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Frontend Commands

```bash
cd frontend

# Run dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Type check
npx tsc --noEmit

# Run E2E tests (needs running dev server)
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run Lighthouse performance audit
npm run lighthouse
```

---

## Deployment Guide (Go Live!)

### Step 1: Push to GitHub

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit: full-stack portfolio"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/portfolio.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Database (Supabase — Free)

1. Go to [supabase.com](https://supabase.com) → Create new project
2. Wait for project to be ready (~2 minutes)
3. Go to **Settings → Database → Connection string → URI**
4. Copy the URI, replace `[YOUR-PASSWORD]` with your DB password
5. Change `postgresql://` to `postgresql+asyncpg://` at the start
6. Save this URL — you'll use it in Railway

### Step 3: Deploy Redis (Upstash — Free)

1. Go to [upstash.com](https://upstash.com) → Create Redis Database
2. Select region closest to you (e.g., Mumbai for India)
3. Copy the **Redis URL** (starts with `rediss://`)
4. Save this URL — you'll use it in Railway

### Step 4: Deploy Backend (Railway — Free)

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select your repo → Select `backend` folder as root directory
3. Add environment variables (Railway dashboard → Variables):

```env
DATABASE_URL=postgresql+asyncpg://postgres:xxx@db.xxx.supabase.co:5432/postgres
REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
SECRET_KEY=<generate with: openssl rand -hex 32>
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-domain.vercel.app
ADMIN_EMAIL=your-email@gmail.com
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=ghp_xxx
```

4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add health check: `/health`
6. Deploy! Railway gives you a URL like `portfolio-backend-xxx.up.railway.app`

### Step 5: Deploy Frontend (Vercel — Free)

1. Go to [vercel.com](https://vercel.com) → Import GitHub repo
2. Set root directory: `frontend`
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://portfolio-backend-xxx.up.railway.app
   ```
4. Deploy! Vercel gives you URL like `your-portfolio.vercel.app`

### Step 6: Run Database Migrations

```bash
# Set production DATABASE_URL temporarily
export DATABASE_URL="postgresql+asyncpg://postgres:xxx@db.xxx.supabase.co:5432/postgres"

cd backend
source venv/bin/activate
alembic upgrade head
```

### Step 7: Custom Domain (Optional — ₹500/year)

1. Buy domain from [Namecheap](https://namecheap.com) (e.g., `yourname.dev`)
2. In Vercel: Settings → Domains → Add `yourname.dev`
3. In Namecheap DNS: Add CNAME record pointing to Vercel
4. Update `CORS_ORIGINS` in Railway to include your new domain

---

## How CI/CD Works

When you push code to GitHub:

```
Push to main branch
       │
       ▼
GitHub Actions triggers automatically:
       │
       ├── Backend Tests (parallel)
       │   ├── Spin up PostgreSQL + Redis
       │   ├── Install Python dependencies
       │   ├── Run ruff lint check
       │   └── Run pytest (55+ tests)
       │
       ├── Frontend Checks (parallel)
       │   ├── Install Node dependencies
       │   ├── Run ESLint
       │   ├── Run TypeScript type check
       │   └── Run production build
       │
       └── If all pass:
           ├── Deploy backend to Railway (auto)
           └── Deploy frontend to Vercel (auto)
```

---

## Features Overview

### For Visitors (Public)
- Beautiful hero section with animations
- Projects showcase with filter by tech/status
- Blog with search, tags, reading time
- Contact form (with bot protection)
- Dark mode toggle
- Fully responsive (mobile, tablet, desktop)
- PWA — installable on phone home screen
- Works offline (cached pages visible)

### For You (Admin)
- Admin dashboard with analytics
- Create/Edit/Delete projects
- Create/Edit/Delete blog posts (with revision history)
- View contact messages
- Real-time visitor stats (WebSocket)
- Feature flag management

### Production Patterns (What Makes It MNC-Level)
- Circuit Breaker for external service resilience
- Token Bucket rate limiting (not basic counting)
- Idempotency keys (safe retries)
- Cursor-based pagination (fast at any depth)
- Domain Event Bus (loose coupling)
- Content versioning with diff and rollback
- Full-text search with fuzzy matching
- WebSockets for real-time updates
- Feature flags with percentage rollouts
- Graceful shutdown (zero-downtime deploys)
- Structured logging + Prometheus metrics
- PWA + Service Worker + Background Sync

---

## Common Issues & Fixes

### "ModuleNotFoundError" in backend
```bash
cd backend
source venv/bin/activate  # Make sure virtualenv is active
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

### "Port 3000 already in use"
```bash
lsof -ti:3000 | xargs kill -9
```

### Database connection failed
```bash
# If using Docker:
docker ps  # Check if postgres container is running
docker-compose up -d db  # Start just the database

# If using Supabase:
# Check your DATABASE_URL in backend/.env
# Make sure it starts with postgresql+asyncpg://
```

### Redis connection failed
```bash
# If using Docker:
docker ps  # Check if redis container is running
docker-compose up -d redis

# If using Upstash:
# Check your REDIS_URL in backend/.env
# Make sure it starts with rediss:// (with double 's' for TLS)
```

### Frontend can't reach backend
```bash
# Check if backend is running: curl http://localhost:8000/health
# Check frontend/.env.local has: NEXT_PUBLIC_API_URL=http://localhost:8000
# Restart frontend after changing .env.local
```

### Alembic migration errors
```bash
cd backend
source venv/bin/activate

# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head

# If tables already exist:
alembic stamp head  # Mark current state as latest
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14 | SSR, ISR, App Router, best React framework |
| Styling | Tailwind CSS | Utility-first, no CSS files needed |
| Animation | Framer Motion | Production-ready React animations |
| State | Zustand + React Query | Simple store + server state caching |
| Backend | FastAPI | Fastest Python framework, auto-docs |
| ORM | SQLAlchemy (async) | Type-safe DB queries, migration support |
| Database | PostgreSQL | Best relational DB, full-text search built-in |
| Cache | Redis | In-memory store for rate limits, sessions, cache |
| Auth | JWT + OAuth | Industry standard, stateless, scalable |
| Testing | Pytest + Playwright | Unit + E2E coverage |
| CI/CD | GitHub Actions | Free, integrated with GitHub |
| Frontend Host | Vercel | Edge CDN, instant deploys, free |
| Backend Host | Railway | Docker support, auto-deploy, free tier |
| Database Host | Supabase | Managed PostgreSQL, generous free tier |
| Redis Host | Upstash | Serverless Redis, free tier |

---

## Learning Resources

If you want to understand HOW each part works in detail, read:

- **`PORTFOLIO_BOOK.md`** — 29-chapter technical book explaining every pattern with diagrams
- **`DEPLOYMENT.md`** — Detailed deployment guide with troubleshooting
- **`backend/app/main.py`** — Start here to understand backend flow
- **`frontend/src/app/page.tsx`** — Start here for frontend
- **`http://localhost:8000/docs`** — Interactive API documentation

---

## License

MIT License — use this project however you want.

---

**Built with by a developer who believes your code should speak louder than your resume.**
