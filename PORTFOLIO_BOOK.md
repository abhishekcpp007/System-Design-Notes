# Portfolio Website - Complete Technical Book

## The Architecture Bible: From Zero to Production

---

# Table of Contents

## Part 1: Core Architecture (Chapters 1-17)

1. [Introduction & Philosophy](#1-introduction--philosophy)
2. [System Architecture](#2-system-architecture)
3. [Backend Deep Dive](#3-backend-deep-dive)
4. [Authentication & Security](#4-authentication--security)
5. [Database Design](#5-database-design)
6. [API Controllers & Routes](#6-api-controllers--routes)
7. [Services & Business Logic](#7-services--business-logic)
8. [Middleware Pipeline](#8-middleware-pipeline)
9. [Frontend Architecture](#9-frontend-architecture)
10. [State Management & Data Flow](#10-state-management--data-flow)
11. [UI Components & Animations](#11-ui-components--animations)
12. [Admin Dashboard](#12-admin-dashboard)
13. [Testing Strategy](#13-testing-strategy)
14. [CI/CD Pipeline](#14-cicd-pipeline)
15. [Deployment Guide](#15-deployment-guide)
16. [Performance & SEO](#16-performance--seo)
17. [Monitoring & Maintenance](#17-monitoring--maintenance)

## Part 2: Production-Grade Patterns (Chapters 18-29)

18. [Circuit Breaker & Resilience](#18-circuit-breaker--resilience)
19. [Domain Event Bus](#19-domain-event-bus)
20. [Token Bucket Rate Limiting](#20-token-bucket-rate-limiting)
21. [Cursor Pagination & Database Optimization](#21-cursor-pagination--database-optimization)
22. [Idempotency & Safe Retries](#22-idempotency--safe-retries)
23. [WebSockets & Real-time Features](#23-websockets--real-time-features)
24. [Feature Flags & Progressive Rollouts](#24-feature-flags--progressive-rollouts)
25. [Content Versioning & Revision History](#25-content-versioning--revision-history)
26. [Observability: Logging, Metrics & Tracing](#26-observability-logging-metrics--tracing)
27. [PWA, Service Workers & Offline Support](#27-pwa-service-workers--offline-support)
28. [Full-Text Search & Autocomplete](#28-full-text-search--autocomplete)
29. [Graceful Shutdown & Zero-Downtime Deploys](#29-graceful-shutdown--zero-downtime-deploys)

---

# 1. Introduction & Philosophy

## Why This Architecture?

This portfolio website is designed with **enterprise-grade architecture** — the same patterns used by companies like Google, Netflix, and Stripe. The goal is not just to showcase projects, but to showcase **HOW you build software**.

### Design Principles

1. **Separation of Concerns** — Each layer has one job. Controllers handle HTTP, Services handle logic, Models handle data.
2. **Defense in Depth** — Security is not one layer, it's multiple layers. Even if one breaks, others protect.
3. **Fail Gracefully** — Every error is caught, logged, and presented properly to the user.
4. **Type Safety** — TypeScript on frontend, Pydantic on backend. Bugs caught at compile time, not runtime.
5. **Scalability** — Architecture can handle 10 users or 10,000 users without rewrite.

### How It All Connects (The Big Picture)

```
User's Browser
     │
     ├── Request: GET /projects
     │
     ▼
[Vercel CDN] ─── Static assets served from edge (fast!)
     │
     ├── Dynamic request? Forward to Next.js server
     │
     ▼
[Next.js Server Components]
     │
     ├── Needs data? Call Backend API
     │
     ▼
[FastAPI Backend on Railway]
     │
     ├── Middleware Pipeline (runs in ORDER):
     │   1. CORS Check → Is this request from allowed origin?
     │   2. Rate Limiter → Is this IP sending too many requests?
     │   3. Auth Middleware → Is the JWT token valid?
     │   4. Request Logging → Log this request for monitoring
     │
     ├── Controller (Route Handler):
     │   → Validates input (Pydantic schema)
     │   → Calls Service layer
     │   → Returns response
     │
     ├── Service Layer:
     │   → Business logic lives here
     │   → Calls Repository/Model layer
     │   → Handles edge cases
     │
     ├── Model/Repository Layer:
     │   → Talks to PostgreSQL via SQLAlchemy ORM
     │   → No raw SQL (prevents injection)
     │
     ▼
[PostgreSQL on Supabase] ← Stores all persistent data
[Redis on Upstash] ← Stores rate limits, sessions, cache
```

---

# 2. System Architecture

## Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                            │
├──────────────────────────────────────────────────────────────┤
│  Next.js 14 App Router                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │  Pages  │ │Components│ │  Hooks  │ │  API Client     │   │
│  │(Server) │ │(Client)  │ │(Custom) │ │  (Axios/Fetch)  │   │
│  └─────────┘ └─────────┘ └─────────┘ └────────┬────────┘   │
└────────────────────────────────────────────────┼─────────────┘
                                                 │ HTTPS
┌────────────────────────────────────────────────▼─────────────┐
│                        API LAYER                              │
├──────────────────────────────────────────────────────────────┤
│  FastAPI Application                                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Middleware Stack                                        │ │
│  │  [CORS] → [RateLimit] → [Auth] → [Logging]             │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Auth Route│ │Project   │ │Blog Route│ │Analytics     │   │
│  │/api/auth │ │/api/proj │ │/api/blog │ │/api/analytics│   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       └─────────────┼────────────┼───────────────┘           │
│                     ▼                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Service Layer (Business Logic)                          │ │
│  │  AuthService | ProjectService | BlogService | Analytics  │ │
│  └──────────────────────────┬──────────────────────────────┘ │
└─────────────────────────────┼────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                        DATA LAYER                             │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  PostgreSQL    │  │   Redis     │  │  Supabase        │  │
│  │  (Supabase)   │  │  (Upstash)  │  │  Storage (Files) │  │
│  │               │  │             │  │                  │  │
│  │  - Users      │  │  - Sessions │  │  - Images        │  │
│  │  - Projects   │  │  - Rate     │  │  - Resumes       │  │
│  │  - Blogs      │  │    Limits   │  │  - Thumbnails    │  │
│  │  - Contacts   │  │  - Cache    │  │                  │  │
│  │  - Analytics  │  │             │  │                  │  │
│  └────────────────┘  └─────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### Example 1: User Visits Projects Page (No Auth Required)

```
1. Browser → GET https://yourname.dev/projects
2. Vercel CDN checks: Is this page cached? 
   → YES: Serve cached HTML (super fast, <50ms)
   → NO: Forward to Next.js server

3. Next.js Server Component runs:
   → fetch("https://api.yourname.dev/api/v1/projects?published=true")

4. FastAPI receives request:
   → CORS middleware: ✅ Origin is allowed
   → Rate Limiter: ✅ Under limit (100 req/min)
   → Auth: ⏭️ Skipped (public endpoint)
   → Controller: projects_router.get_all()

5. Controller calls ProjectService.get_published_projects()

6. Service calls DB: SELECT * FROM projects WHERE published=true ORDER BY order

7. Response flows back:
   DB → Service → Controller → JSON Response → Next.js → HTML → Browser

8. Next.js caches the rendered page for 60 seconds (ISR)
   → Next visitor gets instant cached response
```

### Example 2: Admin Adds New Project (Auth Required)

```
1. Admin clicks "Add Project" in dashboard
2. Browser → POST https://api.yourname.dev/api/v1/projects
   Headers: { Authorization: "Bearer eyJhbG..." }
   Body: { title: "My App", description: "...", tech_stack: [...] }

3. FastAPI middleware pipeline:
   → CORS: ✅ Allowed origin
   → Rate Limiter: ✅ Under limit
   → Auth Middleware: 
     → Extract token from header
     → Decode JWT → verify signature → check expiry
     → Attach user to request: request.state.user = {id: 1, role: "admin"}

4. Controller: projects_router.create_project()
   → Check: request.state.user.role == "admin"? ✅
   → Validate body with Pydantic schema
   → Call ProjectService.create(data)

5. Service:
   → Sanitize input (strip HTML tags)
   → Generate slug from title
   → Upload thumbnail to Supabase Storage
   → Insert into database
   → Invalidate Redis cache for projects list
   → Return created project

6. Controller returns: 201 Created + project JSON

7. Frontend receives response → Updates UI → Shows success toast
```

### Example 3: Login Flow (Most Complex)

```
1. User submits login form
   → POST /api/v1/auth/login
   → Body: { email: "user@email.com", password: "SecurePass123!" }

2. Rate Limiter checks:
   → Redis: INCR login_attempts:{ip} → current count
   → If count > 5 in last minute → 429 Too Many Requests
   → Set TTL 60 seconds on the key

3. Auth Controller: auth_router.login()
   → Validate with LoginSchema (email format, password not empty)
   → Call AuthService.authenticate(email, password)

4. AuthService.authenticate():
   → Query DB: SELECT * FROM users WHERE email = ? AND is_active = true
   → If not found → raise InvalidCredentials (generic message, don't reveal if email exists)
   → Verify password: bcrypt.verify(password, user.password_hash)
   → If wrong → raise InvalidCredentials
   → If correct → continue

5. Generate Tokens:
   → Access Token: JWT with {user_id, role, exp: now+15min}
     signed with SECRET_KEY using HS256 algorithm
   → Refresh Token: Random 64-char string
     stored in DB: INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
     (we store HASH of token, not token itself — so even if DB leaks, tokens are safe)

6. Set Refresh Token Cookie:
   → Set-Cookie: refresh_token=abc123; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800
   → HttpOnly: JavaScript CANNOT read this cookie (XSS protection)
   → Secure: Only sent over HTTPS
   → SameSite=Strict: Not sent on cross-site requests (CSRF protection)

7. Response: { access_token: "eyJhbG...", user: { id, email, role } }

8. Frontend stores access_token in memory (React state/context)
   → NOT in localStorage (vulnerable to XSS)
   → NOT in sessionStorage (vulnerable to XSS)
   → In JavaScript variable → dies when tab closes (safest)

9. All subsequent requests include:
   → Header: Authorization: Bearer {access_token}

10. When access token expires (after 15 min):
    → API returns 401
    → Frontend interceptor catches 401
    → Calls POST /api/v1/auth/refresh (cookie auto-sent)
    → Backend verifies refresh token → issues new access + refresh tokens
    → OLD refresh token marked as REVOKED in DB
    → Retry original request with new access token
    → User doesn't notice anything (seamless)
```

---

# 3. Backend Deep Dive

## Project Structure Explained

```
backend/
├── app/
│   ├── __init__.py          # Makes this a Python package
│   ├── main.py              # App entry point - creates FastAPI instance, registers routes
│   ├── config.py            # All settings from environment variables (never hardcoded)
│   ├── database.py          # Database connection setup, session management
│   │
│   ├── models/              # SQLAlchemy ORM Models (Database tables as Python classes)
│   │   ├── __init__.py      # Exports all models
│   │   ├── user.py          # User table
│   │   ├── project.py       # Project table
│   │   ├── blog.py          # Blog post table
│   │   ├── contact.py       # Contact message table
│   │   ├── analytics.py     # Page view tracking table
│   │   └── refresh_token.py # Refresh token storage table
│   │
│   ├── schemas/             # Pydantic Schemas (Request/Response validation)
│   │   ├── __init__.py
│   │   ├── auth.py          # LoginRequest, SignupRequest, TokenResponse
│   │   ├── project.py       # ProjectCreate, ProjectUpdate, ProjectResponse
│   │   ├── blog.py          # BlogCreate, BlogUpdate, BlogResponse
│   │   ├── contact.py       # ContactCreate, ContactResponse
│   │   └── analytics.py     # AnalyticsResponse, PageViewCreate
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # Dependency injection (get_db, get_current_user, etc.)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # Main router - includes all sub-routers
│   │       ├── auth.py      # Auth endpoints (login, signup, refresh, logout)
│   │       ├── projects.py  # Project CRUD endpoints
│   │       ├── blog.py      # Blog CRUD endpoints
│   │       ├── contact.py   # Contact form endpoint
│   │       ├── analytics.py # Analytics endpoints
│   │       └── admin.py     # Admin-only endpoints
│   │
│   ├── services/            # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py  # Authentication logic
│   │   ├── project_service.py
│   │   ├── blog_service.py
│   │   ├── contact_service.py
│   │   ├── analytics_service.py
│   │   ├── email_service.py # Send emails via Resend
│   │   └── github_service.py # Fetch GitHub stats
│   │
│   ├── middleware/          # Request/Response processing
│   │   ├── __init__.py
│   │   ├── rate_limiter.py  # Redis-based rate limiting
│   │   ├── cors.py          # CORS configuration
│   │   └── security.py      # Security headers (CSP, HSTS, etc.)
│   │
│   └── utils/               # Shared utilities
│       ├── __init__.py
│       ├── security.py      # Password hashing, JWT encode/decode
│       ├── validators.py    # Custom validation helpers
│       └── exceptions.py    # Custom exception classes
│
├── migrations/              # Alembic database migrations
│   ├── env.py
│   ├── versions/            # Each migration file = one schema change
│   └── alembic.ini
│
├── tests/                   # Test files mirror app structure
│   ├── conftest.py          # Shared test fixtures
│   ├── test_auth.py
│   ├── test_projects.py
│   └── test_blog.py
│
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── .env.example            # Template for environment variables
```

## How main.py Works (The Entry Point)

```python
# app/main.py - This is where everything starts

"""
FLOW:
1. FastAPI() creates the application instance
2. We add middleware in ORDER (first added = first executed)
3. We include routers (groups of endpoints)
4. Lifespan events handle startup/shutdown tasks
"""

# When the server starts:
# 1. Python imports this file
# 2. FastAPI creates the app
# 3. @app.on_event("startup") connects to database and redis
# 4. Middleware is registered
# 5. Routes are registered
# 6. Uvicorn starts serving HTTP requests

# When a request comes in:
# 1. SecurityHeadersMiddleware adds protective headers
# 2. RateLimitMiddleware checks Redis for request count
# 3. CORSMiddleware checks if origin is allowed
# 4. Request reaches the matching route handler
# 5. Dependency injection provides db session, current user, etc.
# 6. Handler executes and returns response
# 7. Response flows back through middleware (can modify response too)
```

## How config.py Works (Settings Management)

```python
# app/config.py

"""
WHY: Never hardcode secrets. Environment variables keep secrets safe.

HOW IT WORKS:
- Pydantic BaseSettings reads from environment variables
- In development: reads from .env file
- In production: reads from Railway/Vercel environment settings
- Type validation ensures all settings are correct format
- Missing required settings = app won't start (fail fast)

SECURITY:
- .env file is in .gitignore (never committed)
- .env.example shows structure without real values
- Each environment (dev/staging/prod) has different values
"""
```

## How database.py Works (Connection Management)

```python
# app/database.py

"""
WHAT: Manages PostgreSQL connections using SQLAlchemy

HOW:
- create_async_engine() → Creates a connection POOL (not just one connection)
  → Pool reuses connections (creating new ones is expensive)
  → Default: 5 connections, max 10
  
- AsyncSession → Each request gets ONE session from the pool
  → Session = a "conversation" with the database
  → Auto-committed on success, auto-rolled-back on error
  
- get_db() dependency → FastAPI injects database session into route handlers
  → yield pattern ensures session is ALWAYS closed after request
  → Even if the handler throws an error

WHY ASYNC:
- Synchronous: Handler waits for DB query → can't serve other requests
- Asynchronous: Handler awaits DB query → serves other requests while waiting
- Result: 10x more concurrent users with same resources
"""
```

---

# 4. Authentication & Security

## The Complete Auth Architecture

### Password Storage (Never Plain Text!)

```
User password: "MySecure123!"

Step 1: Generate salt (random bytes)
Step 2: Hash = bcrypt(password + salt, rounds=12)
Step 3: Store hash in database (salt is embedded in hash)

Result stored: "$2b$12$LJ3m4ks92h3..."

WHY bcrypt:
- Intentionally SLOW (takes ~250ms to compute)
- Attacker trying 1 billion passwords? Would take 7,900 YEARS
- Compare: MD5 takes 0.000001ms → 1 billion passwords in 16 minutes
- Salt prevents rainbow table attacks (pre-computed hash databases)
```

### JWT Token Structure

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.  ← Header (algorithm + type)
eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4i.  ← Payload (user data)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_ad.  ← Signature (verification)

Header (decoded): { "alg": "HS256", "typ": "JWT" }
Payload (decoded): { "user_id": 1, "role": "admin", "exp": 1700000000 }
Signature: HMAC-SHA256(header + "." + payload, SECRET_KEY)

HOW VERIFICATION WORKS:
1. Receive token from client
2. Split into 3 parts
3. Recompute signature using OUR secret key
4. Compare with received signature
5. If match → token is authentic (not tampered)
6. Check exp claim → if past current time → token expired

WHY THIS IS SECURE:
- Without SECRET_KEY, impossible to create valid signature
- Changing ANY byte in payload → signature won't match
- Expiry ensures stolen tokens become useless quickly
```

### Refresh Token Rotation (Advanced Security)

```
PROBLEM: Access token expires every 15 min. User has to login every 15 min?
SOLUTION: Refresh tokens (live 7 days) can get new access tokens.

BUT: What if refresh token is stolen?
SOLUTION: Token Rotation

HOW IT WORKS:
┌────────────────────────────────────────────────┐
│ Initial Login:                                  │
│   → Issue: Access Token A1 + Refresh Token R1  │
│   → Store in DB: { token_hash: hash(R1),       │
│                     user_id: 1,                 │
│                     is_revoked: false }         │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ After 15 min (A1 expired):                     │
│   → Client sends R1 to /auth/refresh           │
│   → Backend: verify R1 exists and not revoked  │
│   → REVOKE R1 (is_revoked = true)             │
│   → Issue: NEW Access Token A2 + NEW Refresh R2│
│   → Store R2 in DB                             │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ If attacker steals R1 and tries to use it:     │
│   → R1 is already REVOKED → request denied     │
│   → Alert: potential token theft!              │
│   → Revoke ALL tokens for this user (nuclear)  │
│   → User must login again                      │
└────────────────────────────────────────────────┘
```

### OAuth Flow (Google/GitHub Login)

```
WHY OAuth: Users don't want to create yet another password.
SECURITY: We NEVER see their Google/GitHub password.

┌──────────────────────────────────────────────────────────────┐
│ Step 1: User clicks "Login with GitHub"                       │
│   → Frontend redirects to:                                    │
│     https://github.com/login/oauth/authorize?                 │
│       client_id=YOUR_APP_ID&                                  │
│       redirect_uri=https://yoursite.dev/auth/callback&         │
│       scope=read:user,user:email&                             │
│       state=random_csrf_token                                 │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 2: User authorizes on GitHub's page                      │
│   → GitHub redirects back to YOUR callback URL with CODE     │
│     https://yoursite.dev/auth/callback?code=abc123&state=...  │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 3: Backend exchanges code for access token               │
│   → POST https://github.com/login/oauth/access_token         │
│     Body: { client_id, client_secret, code }                 │
│   → GitHub returns: { access_token: "gho_xxxx" }            │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 4: Backend fetches user profile                          │
│   → GET https://api.github.com/user                          │
│     Headers: { Authorization: "token gho_xxxx" }             │
│   → Gets: { name, email, avatar_url }                        │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 5: Create or find user in OUR database                   │
│   → SELECT * FROM users WHERE oauth_provider='github'        │
│     AND oauth_id='12345'                                      │
│   → If exists: login them                                     │
│   → If new: create account (no password needed)              │
│   → Issue our own JWT tokens (same as normal login)          │
└──────────────────────────────────────────────────────────────┘
```

---

# 5. Database Design

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐
│    Users     │       │  Refresh Tokens  │
├──────────────┤       ├──────────────────┤
│ id (PK)      │───┐   │ id (PK)          │
│ email        │   │   │ user_id (FK)─────┤───→ Users.id
│ password_hash│   │   │ token_hash       │
│ full_name    │   │   │ expires_at       │
│ role         │   │   │ is_revoked       │
│ avatar_url   │   │   │ created_at       │
│ oauth_provider│  │   └──────────────────┘
│ oauth_id     │   │
│ is_active    │   │   ┌──────────────────┐
│ created_at   │   │   │    Projects      │
│ last_login   │   │   ├──────────────────┤
└──────────────┘   │   │ id (PK)          │
                   │   │ user_id (FK)─────┤───→ Users.id (who created)
                   │   │ title            │
                   │   │ slug             │
                   │   │ description      │
                   │   │ long_description │
                   │   │ tech_stack[]     │
                   │   │ github_url       │
                   │   │ live_url         │
                   │   │ thumbnail_url    │
                   │   │ category         │
                   │   │ featured         │
                   │   │ display_order    │
                   │   │ published        │
                   │   │ created_at       │
                   │   │ updated_at       │
                   │   └──────────────────┘
                   │
                   │   ┌──────────────────┐
                   │   │   Blog Posts     │
                   │   ├──────────────────┤
                   │   │ id (PK)          │
                   └──▶│ author_id (FK)   │
                       │ title            │
                       │ slug             │
                       │ content          │
                       │ excerpt          │
                       │ tags[]           │
                       │ published        │
                       │ views_count      │
                       │ reading_time     │
                       │ created_at       │
                       │ updated_at       │
                       └──────────────────┘

┌──────────────────┐   ┌──────────────────┐
│  Contact Messages│   │   Page Views     │
├──────────────────┤   ├──────────────────┤
│ id (PK)          │   │ id (PK)          │
│ name             │   │ page_path        │
│ email            │   │ visitor_hash     │
│ subject          │   │ country          │
│ message          │   │ device_type      │
│ is_read          │   │ browser          │
│ is_replied       │   │ referrer         │
│ created_at       │   │ created_at       │
└──────────────────┘   └──────────────────┘
```

## Why These Design Decisions?

### 1. `password_hash` not `password`
- NEVER store plain passwords
- Even if database is hacked, passwords are safe
- bcrypt hash is one-way (cannot reverse)

### 2. `slug` field on projects and blogs
- URL-friendly: `/projects/my-awesome-app` instead of `/projects/123`
- Better SEO (Google loves descriptive URLs)
- Human-readable (users know what they'll see)

### 3. `tech_stack[]` as array
- PostgreSQL supports array columns natively
- Filter projects by technology: `WHERE 'React' = ANY(tech_stack)`
- No need for separate many-to-many table (simpler)

### 4. `visitor_hash` instead of IP address
- Privacy-first: we hash IP + User-Agent → anonymous identifier
- Can count unique visitors WITHOUT storing personal data
- GDPR compliant (no PII stored)

### 5. `is_revoked` on refresh tokens
- Enables instant logout (revoke all tokens)
- Enables token rotation security
- Can see all active sessions

### 6. `display_order` on projects
- Admin can drag-and-drop to reorder projects
- Best projects shown first
- Integer field: 1, 2, 3... (easy to reorder)

---

# 6. API Controllers & Routes

## What is a Controller?

A controller is the **first point of contact** for an incoming HTTP request. Its job:
1. Receive the request
2. Validate input data
3. Call the appropriate service
4. Return the response

**Controllers should be THIN** — no business logic here. Just routing and validation.

## Complete API Endpoints

### Auth Controller (`/api/v1/auth`)

| Method | Endpoint | Auth? | Description |
|--------|----------|-------|-------------|
| POST | `/signup` | No | Create new account |
| POST | `/login` | No | Get access + refresh tokens |
| POST | `/refresh` | Cookie | Get new tokens using refresh token |
| POST | `/logout` | Yes | Revoke refresh token |
| GET | `/me` | Yes | Get current user profile |
| PUT | `/me` | Yes | Update profile |
| POST | `/forgot-password` | No | Send password reset email |
| POST | `/reset-password` | No | Reset password with token |
| GET | `/oauth/github` | No | Initiate GitHub OAuth |
| GET | `/oauth/github/callback` | No | Handle GitHub callback |
| GET | `/oauth/google` | No | Initiate Google OAuth |
| GET | `/oauth/google/callback` | No | Handle Google callback |

### How Auth Controller Works (Detailed)

```python
# POST /api/v1/auth/signup

"""
INPUT: { email, password, full_name }

VALIDATION (Pydantic):
  - email: valid email format
  - password: min 8 chars, has uppercase, lowercase, number, special char
  - full_name: 2-100 characters, no special chars

CONTROLLER FLOW:
  1. Parse request body → SignupSchema validates
  2. Call AuthService.register(data)
  3. Service checks: email already exists? → 409 Conflict
  4. Service hashes password with bcrypt
  5. Service creates user in DB
  6. Service generates tokens
  7. Return 201 + tokens + user data

ERROR RESPONSES:
  - 400: Invalid input (validation failed)
  - 409: Email already registered
  - 429: Too many signup attempts (rate limited)
  - 500: Unexpected server error
"""
```

```python
# POST /api/v1/auth/login

"""
INPUT: { email, password }

SECURITY MEASURES:
  - Rate limited: 5 attempts per minute per IP
  - Constant-time comparison (prevents timing attacks)
  - Generic error message (don't reveal if email exists)
  - Failed attempts logged for monitoring

CONTROLLER FLOW:
  1. Rate limiter checks Redis: login_attempts:{ip}
  2. Parse body → LoginSchema validates
  3. Call AuthService.authenticate(email, password)
  4. Service queries user by email
  5. Service verifies password hash
  6. Service generates access token (JWT, 15 min)
  7. Service generates refresh token (random, 7 days)
  8. Service stores refresh token hash in DB
  9. Set refresh token in HttpOnly cookie
  10. Return 200 + access_token + user data

TIMING ATTACK PREVENTION:
  Even if email doesn't exist, we still run bcrypt.verify()
  against a dummy hash. This ensures the response time is
  the same whether email exists or not. Attacker can't 
  determine valid emails by measuring response time.
"""
```

### Projects Controller (`/api/v1/projects`)

| Method | Endpoint | Auth? | Description |
|--------|----------|-------|-------------|
| GET | `/` | No | List all published projects |
| GET | `/:slug` | No | Get single project by slug |
| POST | `/` | Admin | Create new project |
| PUT | `/:id` | Admin | Update project |
| DELETE | `/:id` | Admin | Delete project |
| PUT | `/reorder` | Admin | Reorder projects |
| GET | `/stats` | Admin | Get project view counts |

### How Projects Controller Works

```python
# GET /api/v1/projects (Public - No Auth)

"""
QUERY PARAMS:
  - category: filter by category (optional)
  - tech: filter by technology (optional)
  - featured: only featured projects (optional)
  - page: pagination page number (default: 1)
  - limit: items per page (default: 10, max: 50)

CONTROLLER FLOW:
  1. Parse query params
  2. Call ProjectService.get_published(filters, pagination)
  3. Service builds query with filters
  4. Service executes with pagination
  5. Return 200 + { projects: [...], total: N, page: 1, pages: 3 }

CACHING:
  - Check Redis first: cache:projects:{hash_of_params}
  - If cached → return cached (no DB query!)
  - If not → query DB → store in Redis (TTL: 5 min) → return
  - On any project create/update/delete → invalidate cache
"""

# POST /api/v1/projects (Admin Only)

"""
INPUT: { title, description, long_description, tech_stack, github_url, live_url, category, featured }

AUTH CHECK:
  1. Extract JWT from Authorization header
  2. Decode → get user_id
  3. Query user from DB → check role == "admin"
  4. If not admin → 403 Forbidden

CONTROLLER FLOW:
  1. Auth dependency verifies admin role
  2. Parse body → ProjectCreateSchema validates
  3. Call ProjectService.create(data, user_id)
  4. Service generates slug: "My App" → "my-app"
  5. Service checks slug uniqueness (append -2 if duplicate)
  6. Service saves to DB
  7. Service invalidates Redis cache
  8. Return 201 + created project

SLUG GENERATION:
  "My Awesome Project!" → "my-awesome-project"
  If "my-awesome-project" exists → "my-awesome-project-2"
"""
```

### Blog Controller (`/api/v1/blog`)

| Method | Endpoint | Auth? | Description |
|--------|----------|-------|-------------|
| GET | `/` | No | List published posts |
| GET | `/:slug` | No | Get single post (increments view) |
| POST | `/` | Admin | Create new post |
| PUT | `/:id` | Admin | Update post |
| DELETE | `/:id` | Admin | Delete post |
| GET | `/tags` | No | Get all unique tags |
| GET | `/search?q=` | No | Full-text search |

### How Blog Controller Works

```python
# GET /api/v1/blog/:slug

"""
SPECIAL BEHAVIOR: Increments view count!

CONTROLLER FLOW:
  1. Get slug from URL path
  2. Call BlogService.get_by_slug(slug)
  3. Service queries DB for post
  4. If not found → 404
  5. If not published and requester is not admin → 404
  6. Service increments view count (background task, doesn't slow response)
  7. Return 200 + post data with reading_time calculated

VIEW COUNT LOGIC (Anti-gaming):
  - Hash visitor's IP + User-Agent → visitor_hash
  - Check Redis: viewed:{post_id}:{visitor_hash}
  - If exists → already counted, don't increment
  - If not → SET with TTL 24h → increment view count
  - Result: Same person viewing 100 times = 1 view count
"""
```

### Contact Controller (`/api/v1/contact`)

| Method | Endpoint | Auth? | Description |
|--------|----------|-------|-------------|
| POST | `/` | No | Submit contact form |
| GET | `/` | Admin | List all messages |
| PUT | `/:id/read` | Admin | Mark as read |
| DELETE | `/:id` | Admin | Delete message |

```python
# POST /api/v1/contact (Public - Heavy Security)

"""
INPUT: { name, email, subject, message }

SECURITY LAYERS:
  1. Rate limit: 3 messages per hour per IP (prevents spam)
  2. Input validation: 
     - name: 2-100 chars, letters and spaces only
     - email: valid format
     - subject: 5-200 chars
     - message: 10-5000 chars
  3. Content sanitization: Strip all HTML tags (prevent stored XSS)
  4. Honeypot field: Hidden field in form - if filled, it's a bot → reject silently

CONTROLLER FLOW:
  1. Rate limiter: Check Redis contact_form:{ip}
  2. Validate with ContactSchema
  3. Check honeypot (if frontend sends hidden field filled → bot)
  4. Sanitize: bleach.clean(message, tags=[], strip=True)
  5. Call ContactService.create(data)
  6. Service saves to DB
  7. Service sends notification email to admin (background task)
  8. Return 201 + { message: "Message sent successfully" }

WHY BACKGROUND TASK FOR EMAIL:
  - Sending email takes 1-3 seconds
  - User shouldn't wait for email to send
  - If email fails, message is still saved in DB
  - Retry logic: try 3 times, then give up
"""
```

### Analytics Controller (`/api/v1/analytics`)

| Method | Endpoint | Auth? | Description |
|--------|----------|-------|-------------|
| POST | `/pageview` | No | Record a page view |
| GET | `/dashboard` | Admin | Get analytics summary |
| GET | `/visitors` | Admin | Get visitor stats |
| GET | `/popular` | Admin | Get popular pages |

```python
# POST /api/v1/analytics/pageview (Called by frontend on every page load)

"""
INPUT: { page_path, referrer }
(Other info extracted from request: IP, User-Agent)

PRIVACY-FIRST APPROACH:
  - We DON'T store IP addresses
  - We DON'T use cookies/fingerprinting
  - We DO hash IP+UA for unique visitor counting
  - We DO detect country from IP (then discard IP)
  - We DO detect device type from User-Agent

CONTROLLER FLOW:
  1. Extract: IP, User-Agent from request headers
  2. Generate visitor_hash: SHA256(IP + User-Agent + daily_salt)
     (daily_salt changes every day → can't track across days)
  3. Detect country: GeoIP lookup (free MaxMind database)
  4. Detect device: Parse User-Agent → mobile/desktop/tablet
  5. Save to DB: { page_path, visitor_hash, country, device_type, referrer }
  6. Return 204 No Content (fire-and-forget from frontend)

WHY daily_salt:
  - Same person visiting today and tomorrow = 2 different hashes
  - We can count unique visitors PER DAY
  - But can't track someone across multiple days
  - Maximum privacy while still useful analytics
"""
```

---

# 7. Services & Business Logic

## What is a Service?

Services contain the **business logic** — the "smart" part of your application. Controllers are dumb (just routing), services are smart (decisions, calculations, rules).

### Service Rules:
1. Services DON'T know about HTTP (no request/response objects)
2. Services DON'T access request headers directly
3. Services CAN call other services
4. Services CAN call the database
5. Services handle edge cases and business rules

## AuthService (Most Complex Service)

```python
# services/auth_service.py

"""
RESPONSIBILITIES:
  - Register new users (with validation)
  - Authenticate users (with security)
  - Manage tokens (create, refresh, revoke)
  - Handle OAuth flows
  - Password reset flow

METHODS:

register(email, password, full_name) → { user, access_token, refresh_token }
  1. Check if email exists → raise EmailAlreadyExists
  2. Validate password strength
  3. Hash password with bcrypt (12 rounds)
  4. Create user in DB
  5. Generate tokens
  6. Send welcome email (background)
  7. Return user + tokens

authenticate(email, password) → { user, access_token, refresh_token }
  1. Find user by email
  2. If not found → run dummy bcrypt.verify (timing attack prevention) → raise InvalidCredentials
  3. Verify password against hash
  4. If wrong → raise InvalidCredentials  
  5. Update last_login timestamp
  6. Generate tokens
  7. Return user + tokens

refresh_tokens(refresh_token_string) → { access_token, refresh_token }
  1. Hash the received token
  2. Find in DB by hash
  3. If not found → raise InvalidToken
  4. If revoked → SECURITY BREACH! Revoke ALL user's tokens → raise TokenReuse
  5. If expired → raise TokenExpired
  6. Revoke current token (mark is_revoked = true)
  7. Generate new token pair
  8. Return new tokens

revoke_all_tokens(user_id) → void
  - UPDATE refresh_tokens SET is_revoked = true WHERE user_id = ? AND is_revoked = false
  - Used for: logout all devices, security breach response

generate_access_token(user) → string
  - Payload: { user_id, role, exp: now + 15min }
  - Sign with HS256 algorithm using SECRET_KEY
  - Return JWT string

generate_refresh_token(user_id) → string
  - Generate: 64 random bytes → hex string
  - Hash it: SHA256(token) → store hash in DB
  - Return: raw token (sent to client)
  - WHY hash in DB: If DB leaks, attacker can't use tokens
"""
```

## ProjectService

```python
# services/project_service.py

"""
METHODS:

get_published(filters, pagination) → { projects, total, page, pages }
  1. Build SQLAlchemy query: published=True
  2. Apply filters (category, tech, featured)
  3. Apply ordering (display_order)
  4. Apply pagination (offset, limit)
  5. Execute count query (for total)
  6. Execute data query
  7. Return paginated response

get_by_slug(slug) → Project
  1. Query by slug
  2. If not found → raise NotFound
  3. Return project

create(data, user_id) → Project
  1. Generate slug from title
  2. Ensure slug uniqueness
  3. Validate URLs (github_url, live_url)
  4. Create in DB
  5. Invalidate cache
  6. Return project

update(project_id, data, user_id) → Project
  1. Find project by ID
  2. If not found → raise NotFound
  3. If title changed → regenerate slug
  4. Update fields
  5. Invalidate cache
  6. Return updated project

delete(project_id) → void
  1. Find project by ID
  2. Delete from DB
  3. Invalidate cache
  4. If has thumbnail → delete from storage

reorder(project_ids: list) → void
  1. Validate all IDs exist
  2. Update display_order for each: index in list = new order
  3. Invalidate cache
"""
```

## EmailService

```python
# services/email_service.py

"""
USES: Resend API (free 100 emails/day)

HOW IT WORKS:
  - Resend provides a simple REST API for sending emails
  - We format HTML email templates
  - Send via background task (don't block the main request)

TEMPLATES:
  - Welcome email (after signup)
  - Contact form notification (to admin)
  - Password reset link
  - New contact message alert

RETRY LOGIC:
  - If send fails → wait 5s → retry
  - Max 3 retries
  - If all fail → log error (don't crash the app)

WHY NOT SMTP:
  - SMTP is complex to configure
  - Resend handles deliverability, spam filtering
  - Free tier is plenty for portfolio (100/day)
  - Simple REST API (one HTTP call)
"""
```

## GitHubService

```python
# services/github_service.py

"""
PURPOSE: Show live GitHub stats on portfolio (real-time flex)

WHAT WE FETCH:
  - Total public repos count
  - Total stars across all repos
  - Total contributions this year
  - Top languages used
  - Recent commits
  - Individual project stars

HOW:
  - GitHub REST API v3 (free, 60 req/hour without auth, 5000 with token)
  - Use personal access token (read-only scope)
  - Cache results in Redis (TTL: 1 hour) — GitHub stats don't change every second

ENDPOINTS USED:
  - GET /users/{username} → profile data
  - GET /users/{username}/repos → list repos
  - GET /repos/{owner}/{repo} → individual repo stats
  - GraphQL API → contribution graph data

CACHING STRATEGY:
  - On first request: fetch from GitHub → store in Redis
  - Next requests: serve from Redis (instant)
  - Every hour: background job refreshes cache
  - If GitHub is down: serve stale cache (better than error)
"""
```

---

# 8. Middleware Pipeline

## What is Middleware?

Middleware is code that runs **between** the request arriving and the controller handling it. Think of it as security checkpoints in an airport.

```
Request arrives
     │
     ▼
[Checkpoint 1: Security Headers] → Adds protective response headers
     │
     ▼
[Checkpoint 2: CORS] → Blocks requests from unknown websites
     │
     ▼
[Checkpoint 3: Rate Limiter] → Blocks too many requests from one IP
     │
     ▼
[Checkpoint 4: Request Logging] → Records who's doing what
     │
     ▼
[Controller handles request]
     │
     ▼
[Logging records response time]
     │
     ▼
Response sent back
```

## Security Headers Middleware

```python
"""
WHAT: Adds HTTP headers that tell browsers to enable security features.

HEADERS WE ADD:

1. X-Content-Type-Options: nosniff
   → Browser won't try to guess file types
   → Prevents: attacker uploads .jpg that's actually .js

2. X-Frame-Options: DENY
   → Our site can't be loaded in an iframe
   → Prevents: clickjacking (invisible iframe trick)

3. X-XSS-Protection: 1; mode=block
   → Browser's built-in XSS filter enabled
   → Prevents: reflected XSS attacks

4. Strict-Transport-Security: max-age=31536000; includeSubDomains
   → Browser MUST use HTTPS for 1 year
   → Prevents: downgrade attacks (forcing HTTP)

5. Content-Security-Policy: default-src 'self'; script-src 'self' cdn.example.com
   → Only load scripts from our domain + trusted CDNs
   → Prevents: injected malicious scripts

6. Referrer-Policy: strict-origin-when-cross-origin
   → Don't leak full URL when linking to external sites
   → Prevents: sensitive URL path leaking

7. Permissions-Policy: camera=(), microphone=(), geolocation=()
   → Disable browser features we don't need
   → Prevents: malicious scripts accessing camera/mic
"""
```

## CORS Middleware

```python
"""
WHAT: Cross-Origin Resource Sharing — controls WHO can call our API.

PROBLEM:
  - Our frontend: https://yourname.dev
  - Our backend: https://api.yourname.dev
  - These are DIFFERENT ORIGINS (different subdomain)
  - By default, browsers BLOCK cross-origin requests (security)

SOLUTION:
  - Backend explicitly says: "I trust requests from https://yourname.dev"
  - Browser sees this → allows the request

CONFIGURATION:
  allowed_origins = ["https://yourname.dev", "http://localhost:3000"]
  allowed_methods = ["GET", "POST", "PUT", "DELETE"]
  allowed_headers = ["Authorization", "Content-Type"]
  allow_credentials = True  (needed for cookies)

HOW BROWSER CHECKS:
  1. Browser sends OPTIONS request FIRST (preflight)
  2. Backend responds with allowed origins
  3. If origin matches → browser sends actual request
  4. If no match → browser BLOCKS (never reaches backend)

WHY "localhost:3000" IN ALLOWED:
  - During development, frontend runs on localhost
  - In production, we remove localhost from the list
  - Different .env for dev and prod handles this
"""
```

## Rate Limiter Middleware

```python
"""
WHAT: Limits how many requests one IP can make in a time window.

WHY:
  - Brute force login: Attacker tries 1000 passwords/second → BLOCKED
  - DDoS: Bot sends 10000 requests/second → BLOCKED
  - Scraping: Bot crawls all our data → SLOWED DOWN

HOW IT WORKS (Token Bucket Algorithm with Redis):

  For each IP + endpoint combination:
  
  Key: rate_limit:{ip}:{endpoint}
  Value: request count in current window

  Algorithm:
  1. Request arrives from IP 1.2.3.4 to /api/v1/projects
  2. Redis: INCR rate_limit:1.2.3.4:/api/v1/projects
  3. If first request → also SET TTL 60 seconds (1 minute window)
  4. If count > limit → return 429 Too Many Requests
  5. Include headers: X-RateLimit-Remaining, X-RateLimit-Reset

DIFFERENT LIMITS PER ENDPOINT:
  /api/v1/auth/login     → 5 per minute (sensitive!)
  /api/v1/auth/signup    → 3 per hour (prevent mass account creation)
  /api/v1/contact        → 3 per hour (prevent spam)
  /api/v1/projects (GET) → 100 per minute (public, be generous)
  /api/v1/* (general)    → 60 per minute (reasonable default)

RESPONSE WHEN BLOCKED:
  HTTP 429 Too Many Requests
  {
    "detail": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
  Headers:
    Retry-After: 45
    X-RateLimit-Limit: 5
    X-RateLimit-Remaining: 0
    X-RateLimit-Reset: 1700000045
"""
```

---

# 9. Frontend Architecture

## Next.js App Router Structure

```
frontend/
├── app/                        # App Router (Next.js 14)
│   ├── layout.tsx              # Root layout (wraps everything)
│   ├── page.tsx                # Home page (/)
│   ├── loading.tsx             # Loading UI for home
│   ├── error.tsx               # Error boundary for home
│   ├── not-found.tsx           # Custom 404 page
│   ├── globals.css             # Global styles
│   │
│   ├── projects/
│   │   ├── page.tsx            # Projects list (/projects)
│   │   └── [slug]/
│   │       └── page.tsx        # Project detail (/projects/my-app)
│   │
│   ├── blog/
│   │   ├── page.tsx            # Blog list (/blog)
│   │   └── [slug]/
│   │       └── page.tsx        # Blog post (/blog/my-post)
│   │
│   ├── contact/
│   │   └── page.tsx            # Contact form (/contact)
│   │
│   ├── auth/
│   │   ├── login/
│   │   │   └── page.tsx        # Login page
│   │   ├── signup/
│   │   │   └── page.tsx        # Signup page
│   │   └── callback/
│   │       └── page.tsx        # OAuth callback handler
│   │
│   └── admin/
│       ├── layout.tsx          # Admin layout (with sidebar)
│       ├── page.tsx            # Dashboard (/admin)
│       ├── projects/
│       │   ├── page.tsx        # Manage projects
│       │   └── new/
│       │       └── page.tsx    # Add project form
│       ├── blog/
│       │   ├── page.tsx        # Manage posts
│       │   └── new/
│       │       └── page.tsx    # Write blog post
│       └── messages/
│           └── page.tsx        # View contact messages
│
├── components/
│   ├── ui/                     # Base UI components (Button, Input, Card, etc.)
│   ├── layout/                 # Layout components (Navbar, Footer, Sidebar)
│   ├── sections/               # Page sections (Hero, About, Skills, etc.)
│   ├── three/                  # Three.js components (3D background)
│   └── shared/                 # Shared components (LoadingSpinner, Toast, etc.)
│
├── hooks/
│   ├── useAuth.ts              # Authentication hook
│   ├── useTheme.ts             # Dark/Light mode hook
│   ├── useMediaQuery.ts        # Responsive breakpoint hook
│   └── useInView.ts            # Scroll animation trigger hook
│
├── lib/
│   ├── api.ts                  # Axios instance with interceptors
│   ├── auth.ts                 # Token management
│   ├── utils.ts                # Utility functions
│   └── constants.ts            # App constants
│
├── providers/
│   ├── AuthProvider.tsx        # Auth context provider
│   ├── ThemeProvider.tsx       # Theme context provider
│   └── ToastProvider.tsx       # Toast notification provider
│
├── styles/
│   └── animations.css          # Custom CSS animations
│
├── public/
│   ├── fonts/                  # Self-hosted fonts
│   ├── images/                 # Static images
│   └── icons/                  # Favicon, app icons
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Server Components vs Client Components

```
RULE: Everything is Server Component by default.
     Add "use client" ONLY when needed.

SERVER COMPONENTS (default):
  ✅ Can fetch data directly (no useEffect needed)
  ✅ Can access database/files directly
  ✅ Zero JavaScript sent to browser (faster!)
  ✅ SEO-friendly (rendered on server)
  
  USE FOR:
  - Pages that display data (projects list, blog posts)
  - Layouts
  - Static content

CLIENT COMPONENTS ("use client"):
  ✅ Can use hooks (useState, useEffect)
  ✅ Can handle events (onClick, onSubmit)
  ✅ Can use browser APIs (localStorage, window)
  ✅ Can animate (Framer Motion)
  
  USE FOR:
  - Interactive forms
  - Animations
  - Theme toggle
  - Navigation with active states
  - Anything with user interaction

PATTERN: Server Component wraps Client Component
  
  // page.tsx (Server - fetches data)
  export default async function ProjectsPage() {
    const projects = await fetchProjects(); // Direct fetch, no hook needed
    return <ProjectGrid projects={projects} />; // Pass data down
  }
  
  // ProjectGrid.tsx (Client - handles interactions)
  "use client"
  export function ProjectGrid({ projects }) {
    const [filter, setFilter] = useState("all");
    // Interactive filtering, animations, etc.
  }
```

## Data Fetching Strategy

```
THREE WAYS TO FETCH DATA:

1. SERVER COMPONENT FETCH (Best for SEO pages)
   - Projects page, Blog page
   - Data fetched at request time on server
   - HTML sent to browser with data already rendered
   - Google can see the content (SEO!)

2. CLIENT-SIDE FETCH (Best for admin/dynamic)
   - Admin dashboard
   - Real-time data (analytics counts)
   - Data that depends on user interaction
   - Uses SWR or React Query for caching

3. STATIC GENERATION (Best for rarely changing content)
   - About page
   - Skills section
   - Content defined at build time
   - Fastest possible (served from CDN)

CACHING:
  - fetch() in Server Components is auto-cached by Next.js
  - Revalidate every 60 seconds: { next: { revalidate: 60 } }
  - Force fresh: { cache: 'no-store' }
  - On-demand revalidation: when admin updates content
```

---

# 10. State Management & Data Flow

## Auth State (Global)

```
HOW AUTH STATE WORKS:

┌─────────────────────────────────────────────────┐
│ AuthProvider (wraps entire app)                   │
│                                                   │
│ State:                                            │
│   user: { id, email, role } | null               │
│   isLoading: boolean                             │
│   isAuthenticated: boolean                       │
│                                                   │
│ Methods:                                          │
│   login(email, password) → stores token in memory│
│   signup(email, password, name)                  │
│   logout() → clears state + revokes token        │
│   refreshToken() → called automatically on 401  │
│                                                   │
│ TOKEN STORAGE:                                    │
│   Access Token → React state (in-memory)         │
│   Refresh Token → HttpOnly cookie (auto-sent)    │
│                                                   │
│ ON APP LOAD:                                      │
│   1. No access token in memory (page refreshed)  │
│   2. Call /auth/refresh (cookie auto-sent)        │
│   3. If valid → get new access token → set user  │
│   4. If invalid → user is logged out             │
└─────────────────────────────────────────────────┘
```

## API Client (Axios with Interceptors)

```
WHAT ARE INTERCEPTORS?
  Code that runs BEFORE every request and AFTER every response.
  Like middleware, but on the frontend.

REQUEST INTERCEPTOR:
  → Runs before EVERY API call
  → Attaches access token: Authorization: Bearer {token}
  → No token? Request goes without (public endpoint)

RESPONSE INTERCEPTOR:
  → Runs after EVERY API response
  → If 401 (Unauthorized):
    1. Pause the failed request
    2. Call /auth/refresh to get new token
    3. Retry the ORIGINAL request with new token
    4. If refresh also fails → logout user
  → If 429 (Rate Limited):
    → Show toast: "Too many requests, try again later"
  → If 500:
    → Show toast: "Something went wrong, please try again"

FLOW DIAGRAM:
  Component → api.get("/projects") 
    → [Request Interceptor adds token]
    → Server
    → [Response Interceptor checks status]
    → Component receives data
```

## Theme State

```
DARK MODE IMPLEMENTATION:

1. Check user preference:
   → localStorage "theme" value?
   → If not → check system: window.matchMedia("(prefers-color-scheme: dark)")
   
2. Apply theme:
   → Add class "dark" to <html> element
   → Tailwind uses dark: prefix for dark styles
   → document.documentElement.classList.add("dark")

3. Store preference:
   → On toggle → save to localStorage
   → On next visit → read from localStorage (instant, no flash)

4. NO FLASH STRATEGY:
   → Inline <script> in layout.tsx (runs before render)
   → Reads localStorage BEFORE React hydrates
   → Applies class immediately
   → User never sees wrong theme flash
```

---

# 11. UI Components & Animations

## Animation Strategy

```
LIBRARIES USED:
  - Framer Motion: Complex animations, page transitions, gestures
  - CSS Animations: Simple hover effects, loading spinners
  - Three.js / React Three Fiber: 3D hero background

PERFORMANCE RULES:
  1. Only animate: transform and opacity (GPU accelerated)
  2. Never animate: width, height, top, left (causes layout reflow)
  3. Use will-change sparingly (GPU memory)
  4. Respect prefers-reduced-motion (accessibility)

SCROLL ANIMATIONS:
  - Intersection Observer detects when element enters viewport
  - Triggers Framer Motion animation
  - Elements animate ONCE (not on scroll up)
  - Stagger: items animate one after another (0.1s delay each)
```

## Component Architecture

```
ATOMIC DESIGN PATTERN:

Atoms (smallest, reusable):
  Button, Input, Badge, Avatar, Skeleton, Tooltip

Molecules (combine atoms):
  Card, FormField (Label + Input + Error), NavLink

Organisms (combine molecules):
  Navbar, ProjectCard, BlogPostCard, ContactForm

Templates (page layouts):
  MainLayout, AdminLayout, AuthLayout

Pages (specific content):
  HomePage, ProjectsPage, AdminDashboard
```

## Hero Section (3D Background)

```
IMPLEMENTATION:

Using React Three Fiber (Three.js for React):
  - Particle system: 1000 floating particles
  - Particles connected by lines when close
  - Mouse movement affects particles (magnetic effect)
  - Subtle color gradient animation
  - Performance: requestAnimationFrame, no re-renders

FALLBACK:
  - If WebGL not supported → CSS gradient animation
  - On mobile → simpler particles (performance)
  - Respects prefers-reduced-motion → static gradient
```

---

# 12. Admin Dashboard

## Features

```
DASHBOARD PAGE (/admin):
  ┌─────────────────────────────────────────────┐
  │  Stats Cards (top)                           │
  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐│
  │  │Visitors│ │Page    │ │Messages│ │Posts ││
  │  │Today:47│ │Views:  │ │Unread:3│ │Total:│ │
  │  │↑12%    │ │152     │ │        │ │12    ││
  │  └────────┘ └────────┘ └────────┘ └──────┘│
  │                                             │
  │  Charts (middle)                            │
  │  ┌──────────────────┐ ┌──────────────────┐ │
  │  │ Visitors (7 days)│ │ Popular Pages    │ │
  │  │  📈 Line Chart   │ │  📊 Bar Chart    │ │
  │  └──────────────────┘ └──────────────────┘ │
  │                                             │
  │  Recent Activity (bottom)                   │
  │  ┌──────────────────────────────────────┐  │
  │  │ • New message from John (2 min ago)  │  │
  │  │ • Blog "React Tips" got 50 views     │  │
  │  │ • New visitor from United States     │  │
  │  └──────────────────────────────────────┘  │
  └─────────────────────────────────────────────┘

PROJECTS MANAGEMENT (/admin/projects):
  - Table with all projects (published/draft)
  - Inline edit, delete, reorder (drag & drop)
  - "Add New" → Full form page
  - Bulk actions (publish, unpublish, delete)

BLOG MANAGEMENT (/admin/blog):
  - MDX editor with live preview
  - Image upload in content
  - Tag management
  - Publish/unpublish toggle
  - View count per post

MESSAGES (/admin/messages):
  - Inbox-style list
  - Unread highlighted
  - Click to expand full message
  - Reply button (opens email client)
  - Delete with confirmation
```

## Admin Route Protection

```
HOW ADMIN PAGES ARE PROTECTED:

1. Server-Side Check (Next.js Middleware):
   → middleware.ts runs BEFORE page loads
   → Checks for valid auth cookie
   → If no cookie → redirect to /auth/login
   → If cookie but not admin → redirect to /

2. Layout-Level Check (Admin Layout):
   → AdminLayout component
   → Calls /api/v1/auth/me to verify token
   → If invalid → redirect to login
   → If valid but role != "admin" → redirect to home

3. API-Level Check (Backend):
   → Even if someone bypasses frontend
   → Backend checks: request.state.user.role == "admin"
   → If not → 403 Forbidden

THREE LAYERS = Hacking from UI is impossible.
Even if someone inspects code and finds /admin URL,
they can't see or modify data without valid admin token.
```

---

# 13. Testing Strategy

## Testing Pyramid

```
        /\
       /  \      E2E Tests (few)
      / E2E\     - Full user flows
     /──────\    - Login → add project → verify
    /        \
   /Integration\  Integration Tests (some)
  /────────────\  - API endpoint tests
 /              \ - Database tests
/   Unit Tests   \ Unit Tests (many)
/────────────────\ - Service logic
                   - Utility functions
                   - Schema validation
```

## Backend Testing (Pytest)

```python
"""
TEST STRUCTURE:

tests/
├── conftest.py       # Shared fixtures (test DB, client, auth tokens)
├── test_auth.py      # Auth endpoint tests
├── test_projects.py  # Project endpoint tests
├── test_blog.py      # Blog endpoint tests
└── test_services/    # Service unit tests

FIXTURES (conftest.py):
  - test_db: Fresh PostgreSQL database for each test
  - client: FastAPI TestClient (makes requests)
  - admin_token: Pre-generated admin JWT for testing
  - sample_project: A project in DB for testing
  
WHAT WE TEST:

1. Happy Path (everything works):
   - POST /signup with valid data → 201, user created
   - POST /login with correct password → 200, token returned
   - GET /projects → 200, list of projects

2. Validation Errors (bad input):
   - POST /signup with invalid email → 422
   - POST /login with short password → 422
   - POST /projects without title → 422

3. Auth Errors (unauthorized):
   - GET /admin without token → 401
   - GET /admin with expired token → 401
   - POST /projects as non-admin → 403

4. Business Logic:
   - Can't signup with existing email → 409
   - Rate limiter blocks after 5 attempts → 429
   - Refresh token rotation works correctly
   - View count increments only once per visitor

5. Edge Cases:
   - Very long input (max length)
   - Unicode characters (emoji in names)
   - Concurrent requests (race conditions)
   - Database down (graceful error)
"""
```

## Frontend Testing (Vitest + Testing Library)

```
WHAT WE TEST:

1. Component Rendering:
   - ProjectCard renders title, description, tags
   - ContactForm renders all fields
   - Admin dashboard shows stats

2. User Interactions:
   - Click filter → projects filter correctly
   - Submit form → validation works
   - Toggle dark mode → class changes

3. API Integration:
   - Mock API calls
   - Loading states show skeleton
   - Error states show error message
   - Success shows data correctly
```

---

# 14. CI/CD Pipeline

## GitHub Actions Workflow

```yaml
# WHAT HAPPENS ON EVERY PUSH:

Push to main branch
       │
       ▼
┌─────────────────────────────┐
│  Job 1: Lint & Type Check   │
│  ──────────────────────────│
│  - ESLint (frontend)        │
│  - Black + Ruff (backend)   │
│  - TypeScript check         │
│  - Mypy (Python types)      │
│                             │
│  FAILS? → Block deployment  │
└──────────────┬──────────────┘
               │ ✅ Pass
               ▼
┌─────────────────────────────┐
│  Job 2: Tests               │
│  ──────────────────────────│
│  - Backend: pytest          │
│  - Frontend: vitest         │
│  - Coverage report          │
│                             │
│  FAILS? → Block deployment  │
└──────────────┬──────────────┘
               │ ✅ Pass
               ▼
┌─────────────────────────────┐
│  Job 3: Security Scan       │
│  ──────────────────────────│
│  - pip audit (Python deps)  │
│  - npm audit (JS deps)      │
│  - Secret scanning          │
│                             │
│  CRITICAL vuln? → Block     │
└──────────────┬──────────────┘
               │ ✅ Pass
               ▼
┌─────────────────────────────┐
│  Job 4: Deploy              │
│  ──────────────────────────│
│  - Backend → Railway        │
│  - Frontend → Vercel        │
│  - Run smoke tests          │
│                             │
│  Auto-deploy on success!    │
└─────────────────────────────┘
```

---

# 15. Deployment Guide

## Step-by-Step Deployment

### 1. Supabase Setup (Database)

```
1. Go to supabase.com → Create account → New project
2. Note down:
   - Database URL (postgres://...)
   - Anon Key (for frontend, limited access)
   - Service Key (for backend, full access) — KEEP SECRET!
3. In SQL editor, our migrations will create tables
4. Enable Row Level Security (RLS) for extra protection
```

### 2. Upstash Setup (Redis)

```
1. Go to upstash.com → Create account → New Redis Database
2. Select region closest to your backend (same as Railway)
3. Note down:
   - UPSTASH_REDIS_URL
   - UPSTASH_REDIS_TOKEN
4. Free tier: 10,000 commands/day (more than enough)
```

### 3. Railway Setup (Backend)

```
1. Go to railway.app → Connect GitHub
2. New Project → Deploy from GitHub repo → Select backend folder
3. Set environment variables:
   - DATABASE_URL=postgres://... (from Supabase)
   - REDIS_URL=redis://... (from Upstash)
   - SECRET_KEY=generate-random-64-char-string
   - CORS_ORIGINS=https://yourname.dev
   - RESEND_API_KEY=...
   - GITHUB_TOKEN=...
4. Set start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
5. Add custom domain: api.yourname.dev
6. Enable auto-deploy from main branch
```

### 4. Vercel Setup (Frontend)

```
1. Go to vercel.com → Connect GitHub
2. Import repository → Select frontend folder
3. Framework Preset: Next.js
4. Set environment variables:
   - NEXT_PUBLIC_API_URL=https://api.yourname.dev
   - NEXT_PUBLIC_SUPABASE_URL=...
   - NEXT_PUBLIC_SUPABASE_ANON_KEY=...
5. Deploy → Get URL: yourname.vercel.app
6. Add custom domain: yourname.dev
7. Enable auto-deploy from main branch
```

### 5. Domain Setup

```
Option A (Free): Use yourname.vercel.app
Option B (Paid ~₹500/year): Buy yourname.dev from Namecheap

DNS Configuration:
  - A record: @ → Vercel IP (76.76.21.21)
  - CNAME: api → railway-app-id.railway.app
  - CNAME: www → yourname.vercel.app
```

---

# 16. Performance & SEO

## Performance Optimizations

```
FRONTEND:
  1. Image Optimization:
     - Next.js Image component (auto WebP, lazy load, responsive sizes)
     - Blur placeholder while loading
     - Priority loading for above-fold images

  2. Code Splitting:
     - Dynamic imports: const ThreeScene = dynamic(() => import("./ThreeScene"), { ssr: false })
     - Only loads Three.js on pages that need it
     - Admin code never loaded for visitors

  3. Font Loading:
     - Self-hosted fonts (no external request)
     - font-display: swap (text visible immediately)
     - Preload critical fonts

  4. Caching:
     - Static pages: cached at CDN edge (instant load)
     - ISR: regenerate every 60 seconds
     - API responses: SWR stale-while-revalidate

BACKEND:
  1. Database:
     - Indexes on frequently queried columns (slug, email, published)
     - Connection pooling (reuse connections)
     - Query optimization (select only needed columns)

  2. Redis Cache:
     - Cache project lists (5 min TTL)
     - Cache GitHub stats (1 hour TTL)
     - Cache blog posts (5 min TTL)

  3. Response:
     - Gzip compression enabled
     - Pagination (never return ALL records)
     - Field selection (only return needed fields)
```

## SEO Strategy

```
1. TECHNICAL SEO:
   - Server-side rendering (Google can read all content)
   - Sitemap.xml (auto-generated)
   - robots.txt (guide search engines)
   - Canonical URLs (prevent duplicate content)
   - Clean URL structure (/projects/my-app, not /projects?id=123)

2. META TAGS (per page):
   - title: "My App - Portfolio | Your Name"
   - description: "A full-stack app built with React and FastAPI..."
   - Open Graph (for sharing on social media):
     - og:title, og:description, og:image
   - Twitter Card: Large image summary

3. STRUCTURED DATA (JSON-LD):
   - Person schema (for your profile)
   - CreativeWork schema (for projects)
   - Article schema (for blog posts)
   - BreadcrumbList (for navigation)
   → Google shows rich results in search!

4. PERFORMANCE (Google ranks fast sites higher):
   - Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
   - Lighthouse score: 95+ across all categories
```

---

# 17. Monitoring & Maintenance

## Error Tracking (Sentry)

```
WHAT: Catches and reports errors in real-time.

BACKEND:
  - Any unhandled exception → sent to Sentry
  - Includes: stack trace, request data, user info
  - Grouped by error type (not 1000 individual alerts)
  - Alerts: Email/Slack on new error type

FRONTEND:
  - React Error Boundaries catch render errors
  - API errors logged
  - Performance monitoring (slow pages flagged)

FREE TIER: 5000 errors/month (plenty for portfolio)
```

## Uptime Monitoring

```
TOOL: UptimeRobot (free)

CHECKS:
  - https://yourname.dev (every 5 min)
  - https://api.yourname.dev/health (every 5 min)

ALERTS:
  - If site down for 5 minutes → email alert
  - Weekly uptime report

/health ENDPOINT:
  Returns 200 if:
  - App is running ✓
  - Database is connected ✓
  - Redis is connected ✓
  
  If any check fails → returns 503
  → UptimeRobot detects → alerts you
```

## Regular Maintenance Checklist

```
WEEKLY:
  □ Check Sentry for new errors
  □ Review contact messages
  □ Check dependency updates (Dependabot PRs)

MONTHLY:
  □ Update dependencies (minor versions)
  □ Review analytics (popular content)
  □ Add new projects/blog posts
  □ Check Lighthouse scores

QUARTERLY:
  □ Major dependency updates
  □ Security audit
  □ Performance review
  □ Backup database
```

---

---

# Part 2: Production-Grade Patterns

> **Note**: These are the same patterns used at Google, Netflix, Uber, and Stripe.
> MNC interviewers specifically ask about these. If you can explain them, you're ahead of 95% candidates.

---

# 18. Circuit Breaker & Resilience

## Simple Explanation

Think of it like a MCB (Miniature Circuit Breaker) in your home's switchboard. When there is overload or short circuit, the MCB trips and cuts the power — it protects your appliances from damage. Same concept in software.

When your app calls GitHub API or sends email via SMTP, and that service goes down — without circuit breaker, your app will keep trying and waiting, making your whole app slow for everyone.

## The Problem Without Circuit Breaker

```
User Request → Your App → GitHub API (DOWN!)
                          ↓
                    Timeout 30 seconds...
                          ↓
                    Error returned to user
                          ↓
Next User Request → Your App → GitHub API (still DOWN!)
                               ↓
                         Again 30 sec wait...

RESULT: Every user waits 30 seconds. App feels dead.
        100 users = 100 hanging connections = server crash possible
```

## How Circuit Breaker Fixes This

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌──────────┐        3 failures        ┌──────────┐                │
│   │  CLOSED  │ ──────────────────────▶  │   OPEN   │                │
│   │(Normal)  │                           │(Blocked) │                │
│   │          │  ◀──────────────────────  │          │                │
│   └──────────┘        success            └──────────┘                │
│        │                  ▲                    │                       │
│        │                  │                    │ after 60 seconds      │
│        │                  │                    ▼                       │
│        │                  │              ┌──────────┐                 │
│        │                  └───────────── │HALF-OPEN │                 │
│        │                   (if probe     │(Testing) │                 │
│        │                    works)       └──────────┘                 │
│        │                                      │                       │
│        │                                      │ if probe fails        │
│        │                                      ▼                       │
│        │                               Back to OPEN                   │
│        │                               (wait longer: exponential)     │
└────────┼─────────────────────────────────────────────────────────────┘
         │
         │  WHAT HAPPENS IN EACH STATE:
         │
         │  CLOSED: All requests pass through normally
         │          If failure count reaches 3 → trip to OPEN
         │
         │  OPEN:   All requests IMMEDIATELY get fallback response
         │          No actual call to external service
         │          Timer starts (60 seconds)
         │
         │  HALF-OPEN: Let 1 test request through
         │             If it succeeds → back to CLOSED (service recovered!)
         │             If it fails → back to OPEN (wait even longer)
```

## Real-World Example in Our App

```
SCENARIO: GitHub API goes down at 2:00 PM

2:00:01 — User visits /projects → GitHub API called → timeout → failure #1
2:00:02 — Another user → GitHub API → timeout → failure #2  
2:00:03 — Another user → GitHub API → timeout → failure #3

🔴 CIRCUIT OPENS! (threshold of 3 reached)

2:00:04 — User visits /projects → Circuit is OPEN → 
           INSTANT response: "GitHub stats temporarily unavailable"
           No waiting! No timeout! User gets response in 5ms.

2:00:05 to 2:01:03 — All requests get instant fallback (no external calls)

2:01:04 — 60 seconds passed → Circuit goes HALF-OPEN
           ONE test request sent to GitHub API
           → If GitHub responds → Circuit CLOSES → normal operation resumes
           → If GitHub still down → Circuit OPENS again → wait 120 sec (exponential backoff)
```

## How We Implemented It

```python
# backend/app/services/circuit_breaker.py

"""
KEY DESIGN DECISIONS:

1. Exponential Backoff: 60s → 120s → 240s → 480s (max)
   Why? If service is down, hammering it every 60s won't help.
   Each failure doubles the wait time.

2. Pre-configured breakers for each service:
   - github_breaker: threshold=3, timeout=60s
     (GitHub goes down rarely, recover fast)
   - smtp_breaker: threshold=3, timeout=120s
     (Email servers can be slow to recover)

3. Metrics tracking:
   - total_calls: how many times service was called
   - total_failures: how many times it failed
   - total_circuit_opens: how many times breaker tripped
   - Used for monitoring dashboards

4. Thread-safe: Uses asyncio locks
   Multiple requests at same time won't cause race conditions
"""
```

## Where MNCs Use This

| Company | Use Case |
|---------|----------|
| Netflix | Hystrix library (now resilience4j) — every microservice call |
| Uber | Payment gateway calls (if Stripe down, don't hang) |
| Amazon | Third-party seller API calls |
| Google | External service dependencies in Cloud Run |

---

# 19. Domain Event Bus

## Simple Explanation

Imagine a college notice board. When placement cell puts a notice, all students see it — HR dept, Training dept, Library — everyone who cares reads it independently. The placement cell doesn't need to go door-to-door informing each department.

Same in code: When something happens (user signs up, contact form submitted), instead of calling 10 different functions one by one, you just "publish" an event. Anyone who cares about that event will automatically react.

## The Problem Without Event Bus

```python
# WITHOUT Event Bus (tightly coupled mess):

async def create_project(data):
    project = await db.insert(data)
    
    # Now we need to do 5 things... all in same function
    await invalidate_cache("projects")          # Cache team wrote this
    await send_notification_to_admin(project)    # Notification team wrote this
    await update_search_index(project)           # Search team wrote this
    await log_to_analytics("project_created")    # Analytics team wrote this
    await broadcast_to_websocket(project)        # Realtime team wrote this
    
    return project

# PROBLEMS:
# 1. If send_notification fails → whole request fails (user sees error)
# 2. Adding new side-effect = changing this function (risky!)
# 3. Testing is nightmare (mock 5 different services)
# 4. This function now takes 2 seconds (all those awaits)
```

## How Event Bus Fixes This

```
┌─────────────────────────────────────────────────────────────────┐
│                      EVENT BUS ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   PUBLISHER                    EVENT BUS              SUBSCRIBERS │
│                                                                   │
│  ┌──────────┐                ┌─────────┐          ┌───────────┐ │
│  │ Create   │  "ProjectCreated"  │         │ ────▶ │ Cache     │ │
│  │ Project  │ ──────────────▶│  BUS    │ ────▶ │ Invalidator│ │
│  │ Handler  │                │         │ ────▶ │ WebSocket  │ │
│  └──────────┘                │(Routes  │ ────▶ │ Notifier   │ │
│                              │ events) │ ────▶ │ Search     │ │
│  ┌──────────┐                │         │          │ Indexer   │ │
│  │ Contact  │  "ContactSubmitted"│     │          └───────────┘ │
│  │ Handler  │ ──────────────▶│         │ ────▶ ┌───────────┐   │
│  └──────────┘                │         │ ────▶ │ Email Job  │   │
│                              │         │ ────▶ │ Admin Alert│   │
│  ┌──────────┐                │         │       └───────────┘   │
│  │ Blog     │  "BlogPublished" │        │                       │
│  │ Handler  │ ──────────────▶│         │ ────▶ ┌───────────┐   │
│  └──────────┘                └─────────┘ ────▶ │ RSS Update │   │
│                                            ────▶ │ Sitemap    │   │
│                                                  └───────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## With Event Bus (Clean Code)

```python
# WITH Event Bus (loosely coupled, beautiful):

async def create_project(data):
    project = await db.insert(data)
    
    # Just publish ONE event — that's it!
    await event_bus.publish(ProjectCreated(
        project_id=project.id,
        title=project.title,
        author_id=current_user.id
    ))
    
    return project  # Returns INSTANTLY

# Subscribers (separate files, separate teams can own them):

@event_bus.subscribe(ProjectCreated)
async def invalidate_project_cache(event):
    await cache.delete_pattern("projects:*")

@event_bus.subscribe(ProjectCreated)
async def notify_via_websocket(event):
    await ws_manager.broadcast("admin", {"new_project": event.title})

@event_bus.subscribe(ProjectCreated)
async def update_search(event):
    await search.index_project(event.project_id)
```

## Key Design Features

```
┌─────────────────────────────────────────────────────────────────┐
│ FEATURE 1: FIRE AND FORGET                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Event handlers run in background (asyncio.create_task)            │
│ Main request does NOT wait for handlers to finish                 │
│                                                                   │
│ User creates project → gets response in 50ms                     │
│ Meanwhile, 5 handlers run in parallel in background              │
│                                                                   │
│ Even if notification handler fails, user already got success!    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FEATURE 2: ERROR ISOLATION                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ If email handler crashes → only email fails                      │
│ Cache handler, WebSocket handler → still work fine               │
│                                                                   │
│ Failed events go to "Dead Letter Queue" for retry later          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FEATURE 3: PRIORITY ORDERING                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Cache invalidation → priority 1 (run first, most important)      │
│ WebSocket notification → priority 5 (nice to have)               │
│ Analytics logging → priority 10 (can be delayed)                 │
│                                                                   │
│ Higher priority handlers run before lower priority ones          │
└─────────────────────────────────────────────────────────────────┘
```

## All Events in Our System

| Event | When It Fires | Handlers |
|-------|---------------|----------|
| `UserCreated` | New signup | Welcome email, analytics |
| `UserLoggedIn` | Login success | Update last_login, analytics |
| `ContactSubmitted` | Contact form | Send email job, admin alert |
| `ProjectCreated` | New project | Cache clear, search index, WS |
| `ProjectUpdated` | Project edit | Cache clear, search reindex |
| `ProjectDeleted` | Project removal | Cache clear, search remove |
| `BlogPostPublished` | Blog goes live | Cache, WS, sitemap, RSS |
| `CacheInvalidated` | Manual/auto | Logging only |
| `FeatureFlagChanged` | Flag update | Broadcast to all admins |

---

# 20. Token Bucket Rate Limiting

## Simple Explanation

Think of a water tank on your building's terrace. It fills slowly (say 1 litre per minute). When you open the tap, water flows out. If you use too much water too fast, the tank empties and you have to wait for it to fill again.

This is exactly Token Bucket — each user has a "bucket" with tokens. Each API request costs 1 token. Tokens refill at a fixed rate. If bucket is empty, request is rejected.

## Why Not Simple Counting? (Old Way vs New Way)

```
OLD WAY (Sliding Window — what we had before):
  "Allow 100 requests per minute"
  
  PROBLEM: Burst at window edge
  
  Time: |-------- minute 1 --------||-------- minute 2 --------|
  Reqs:                    99 reqs↓  ↓99 reqs
                           (at 0:59)  (at 1:00)
  
  User sends 198 requests in 2 seconds! 
  Both pass because they fall in different windows.
  Server overloaded!

NEW WAY (Token Bucket):
  "Bucket holds 30 tokens. Refills at 20/second."
  
  Burst of 30 → allowed (bucket was full)
  Then → must wait for refill (20/sec)
  
  Maximum damage = 30 requests (bucket size)
  Sustained rate = 20/second (refill rate)
  
  MUCH smoother traffic! No edge-case exploits.
```

## Visual Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     TOKEN BUCKET CONCEPT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│    ┌───────────┐                                                 │
│    │  BUCKET   │  capacity = 30 tokens                           │
│    │           │                                                  │
│    │  🪙🪙🪙🪙🪙 │  ← Refill: 20 tokens/second (drip drip)        │
│    │  🪙🪙🪙🪙🪙 │                                                  │
│    │  🪙🪙🪙🪙🪙 │  Current tokens: 15                              │
│    │  🪙🪙🪙🪙🪙 │                                                  │
│    │           │                                                  │
│    │  ───────  │  ← When empty, requests get 429 (Too Many)     │
│    └───────────┘                                                 │
│         │                                                         │
│         │ Each request takes 1 token                             │
│         ▼                                                         │
│    ┌──────────┐                                                  │
│    │  API     │ → Token available? → ✅ Allow request             │
│    │ Request  │ → No tokens left?  → ❌ 429 Too Many Requests    │
│    └──────────┘                                                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Per-Endpoint Rate Limit Policies

```
┌────────────────────────────────────────────────────────────────┐
│ ENDPOINT           │ BURST (bucket) │ SUSTAINED (refill/sec)  │
├────────────────────┼────────────────┼─────────────────────────┤
│ POST /auth/login   │ 5 tokens       │ 5 per minute            │
│ POST /auth/signup  │ 3 tokens       │ 3 per hour              │
│ POST /contact      │ 3 tokens       │ 3 per hour              │
│ GET /search        │ 30 tokens      │ 30 per minute           │
│ Admin endpoints    │ 30 burst       │ 20 sustained per min    │
│ Public GET         │ 100 tokens     │ 100 per minute          │
└────────────────────┴────────────────┴─────────────────────────┘

WHY DIFFERENT LIMITS:
- Login: Low limit → prevents brute force password cracking
- Signup: Very low → prevents spam account creation
- Contact: Very low → prevents spam messages
- Search: Medium → search is expensive (full-text query)
- Admin: Higher → admins are trusted, need to work fast
- Public GET: Generous → we want visitors to browse freely
```

## How It Works with Redis (Atomic Lua Script)

```
WHY LUA SCRIPT?
  Without Lua: GET tokens → calculate → SET tokens = 2 operations
  Between GET and SET, another request might come → RACE CONDITION
  
  With Lua: All logic runs INSIDE Redis in one atomic operation
  No race condition possible. Even with 1000 concurrent requests.

THE ALGORITHM:
  1. Calculate time passed since last request
  2. Add tokens based on refill rate × time passed
  3. Cap at maximum bucket size
  4. Try to consume 1 token
  5. If tokens ≥ 1 → allow, decrement
  6. If tokens < 1 → reject with 429

RESPONSE HEADERS (standard):
  X-RateLimit-Limit: 30          ← Your bucket capacity
  X-RateLimit-Remaining: 17      ← Tokens left right now
  X-RateLimit-Reset: 1700000060  ← When bucket fully refills (Unix timestamp)
  Retry-After: 3                 ← Seconds to wait (only on 429)
```

---

# 21. Cursor Pagination & Database Optimization

## Simple Explanation

You're scrolling Instagram. You see posts 1-20. You scroll down, you see 21-40. How does Instagram know where you left off?

**Old way (Offset)**: "Give me page 5" → DB skips first 40 rows, gives next 10.
**Problem**: On page 5000, DB has to skip 49,990 rows first! Very slow.

**New way (Cursor)**: "Give me 10 items AFTER this timestamp" → DB directly jumps there using index. Fast no matter which page!

## Offset vs Cursor — Visual Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│             OFFSET PAGINATION (The Old Way)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request: GET /projects?page=500&limit=10                        │
│                                                                   │
│  SQL: SELECT * FROM projects ORDER BY id OFFSET 4990 LIMIT 10   │
│                                                                   │
│  What DB does:                                                    │
│  Row 1     → skip                                                │
│  Row 2     → skip                                                │
│  Row 3     → skip                                                │
│  ...                                                              │
│  Row 4990  → skip       ← DB reads ALL these rows for nothing!  │
│  Row 4991  → return ✓                                            │
│  Row 4992  → return ✓                                            │
│  ...                                                              │
│  Row 5000  → return ✓                                            │
│                                                                   │
│  Performance: O(n) — gets SLOWER as page number increases        │
│  Page 1: 2ms | Page 100: 50ms | Page 5000: 2000ms              │
│                                                                   │
│  ALSO: If someone adds/deletes a project between page requests,  │
│  you might see duplicate items or miss items completely!         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│             CURSOR PAGINATION (The Better Way)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request: GET /projects?cursor=eyJpZCI6NDk5MH0&limit=10         │
│                                                                   │
│  Cursor decodes to: { id: 4990 }                                 │
│                                                                   │
│  SQL: SELECT * FROM projects WHERE id > 4990 ORDER BY id LIMIT 10│
│                                                                   │
│  What DB does:                                                    │
│  Jump directly to id=4990 using INDEX (B-tree seek)             │
│  Row 4991  → return ✓                                            │
│  Row 4992  → return ✓                                            │
│  ...                                                              │
│  Row 5000  → return ✓                                            │
│                                                                   │
│  Performance: O(1) — SAME speed no matter how deep you are      │
│  Page 1: 2ms | Page 100: 2ms | Page 5000: 2ms                  │
│                                                                   │
│  BONUS: No duplicate/missing items even with concurrent writes!  │
└─────────────────────────────────────────────────────────────────┘
```

## How Cursor Works (Step by Step)

```
STEP 1: First request (no cursor)
  GET /projects?limit=10
  
  Server returns:
  {
    "data": [project1, project2, ..., project10],
    "next_cursor": "eyJpZCI6MTAsImNyZWF0ZWRfYXQiOiIyMDI0LTAxLTEwIn0=",
    "has_next": true
  }

STEP 2: Client wants next page
  GET /projects?cursor=eyJpZCI6MTAsImNyZWF0ZWRfYXQiOiIyMDI0LTAxLTEwIn0=&limit=10
  
  Server decodes cursor: { id: 10, created_at: "2024-01-10" }
  Server queries: WHERE (created_at, id) > ('2024-01-10', 10) LIMIT 10

STEP 3: Last page
  {
    "data": [project91, project92, project93],
    "next_cursor": null,    ← No more data!
    "has_next": false
  }
```

## Cursor Security (HMAC Integrity)

```
WHY SIGN THE CURSOR?
  Cursor contains: { id: 10, created_at: "2024-01-10" }
  
  Without signing, attacker could send: { id: -1, created_at: "1970-01-01" }
  → Might expose hidden/deleted data!
  
HOW WE SIGN:
  1. cursor_data = base64(json({"id": 10, "created_at": "..."}))
  2. signature = HMAC-SHA256(cursor_data, SECRET_KEY)
  3. final_cursor = cursor_data + "." + signature
  
  Server verifies signature before using cursor.
  If tampered → 400 Bad Request

LIKE: A sealed envelope. If seal is broken, you know someone opened it.
```

## Database Indexes We Added

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDEX OPTIMIZATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Without Index:                                                    │
│   SELECT * FROM projects WHERE published=true                    │
│   → DB scans ALL 10,000 rows (Full Table Scan)                  │
│   → Takes: 500ms                                                 │
│                                                                   │
│ With Index:                                                       │
│   CREATE INDEX idx_projects_published ON projects(published, created_at)│
│   → DB jumps directly to published=true rows (B-tree lookup)    │
│   → Takes: 2ms                                                   │
│                                                                   │
│ It's like: Book without index → read every page to find topic    │
│            Book with index → look up page number, go directly    │
└─────────────────────────────────────────────────────────────────┘

INDEXES WE CREATED:
┌────────────────────────────────────────────────────────────────┐
│ Table        │ Index                        │ Purpose           │
├──────────────┼──────────────────────────────┼───────────────────┤
│ projects     │ (published, featured)        │ Homepage query    │
│ projects     │ (published, created_at DESC) │ Cursor pagination │
│ blog_posts   │ (published, created_at DESC) │ Blog listing      │
│ blog_posts   │ GIN(title) gin_trgm_ops     │ Fuzzy search      │
│ page_views   │ (created_at, page_path)      │ Analytics queries │
│ page_views   │ (visitor_hash)               │ Unique visitors   │
│ refresh_tokens│ (token_hash)                │ Token lookup      │
└──────────────┴──────────────────────────────┴───────────────────┘
```

---

# 22. Idempotency & Safe Retries

## Simple Explanation

You're doing UPI payment. You click "Pay ₹500". Network glitch — you don't see success or failure. You click again. Without idempotency, you'd be charged ₹1000!

Idempotency means: Even if you send the same request 10 times, the effect happens only ONCE. Like pressing elevator button multiple times — lift comes only once.

## The Problem

```
┌─────────────────────────────────────────────────────────────────┐
│                 WITHOUT IDEMPOTENCY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Client: POST /projects (create "My App")                        │
│     │                                                             │
│     ├── Request sent... network timeout... no response           │
│     │                                                             │
│     ├── Client retries: POST /projects (create "My App")         │
│     │                                                             │
│     ▼                                                             │
│  Server created TWO projects with same name! 😱                  │
│                                                                   │
│  OR WORSE:                                                        │
│  POST /contact (send message to admin)                           │
│  → Network issue → retry → admin gets 5 copies of same message  │
└─────────────────────────────────────────────────────────────────┘
```

## The Solution: Idempotency Keys

```
┌─────────────────────────────────────────────────────────────────┐
│                 WITH IDEMPOTENCY KEY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Client generates unique key: "550e8400-e29b-41d4-a716-446655"  │
│                                                                   │
│  Request 1: POST /projects                                       │
│    Headers: { X-Idempotency-Key: "550e8400..." }                │
│    Body: { title: "My App" }                                     │
│                                                                   │
│  Server:                                                          │
│    1. Check Redis: Does key "550e8400..." exist? → NO            │
│    2. Lock the key in Redis (prevent concurrent duplicates)      │
│    3. Process request → Create project → Success (201)           │
│    4. Store response in Redis: key → {status: 201, body: {...}}  │
│    5. Return response to client                                  │
│                                                                   │
│  Request 2 (RETRY — same key):                                   │
│    Headers: { X-Idempotency-Key: "550e8400..." }                │
│                                                                   │
│  Server:                                                          │
│    1. Check Redis: Does key "550e8400..." exist? → YES!          │
│    2. Return STORED response (from first request)                │
│    3. Add header: X-Idempotent-Replayed: true                   │
│    4. Project NOT created again                                  │
│                                                                   │
│  RESULT: Same response, no duplicate. Client happy, server safe. │
└─────────────────────────────────────────────────────────────────┘
```

## Flow Diagram

```
         Client                         Server                    Redis
           │                               │                        │
           │ POST /projects                │                        │
           │ X-Idempotency-Key: abc123    │                        │
           │──────────────────────────────▶│                        │
           │                               │  EXISTS abc123?        │
           │                               │───────────────────────▶│
           │                               │  NO                    │
           │                               │◀───────────────────────│
           │                               │  LOCK abc123           │
           │                               │───────────────────────▶│
           │                               │                        │
           │                               │ [Process Request]      │
           │                               │ [Create Project]       │
           │                               │                        │
           │                               │  STORE response        │
           │                               │───────────────────────▶│
           │    201 Created                │                        │
           │◀──────────────────────────────│                        │
           │                               │                        │
           │ (Network timeout, retry)      │                        │
           │                               │                        │
           │ POST /projects (same key)     │                        │
           │──────────────────────────────▶│                        │
           │                               │  EXISTS abc123?        │
           │                               │───────────────────────▶│
           │                               │  YES → return cached   │
           │                               │◀───────────────────────│
           │    201 Created (replayed)     │                        │
           │◀──────────────────────────────│                        │
           │                               │                        │
```

## Key Design Decisions

```
1. KEY STORAGE: Redis with 24-hour TTL
   → After 24 hours, key is forgotten (saves memory)
   → Same key after 24 hours = new request (acceptable)

2. CONCURRENT REQUESTS: If same key comes while first is processing
   → Return 409 Conflict ("Request already in-flight")
   → Client knows to wait and retry

3. ONLY FOR MUTATIONS: GET requests are naturally idempotent
   → We only check keys on POST, PUT, PATCH, DELETE

4. GRACEFUL FALLBACK: If Redis is down
   → Skip idempotency check (don't break the whole app)
   → Better to have rare duplicates than complete outage

5. HMAC STORAGE KEY: We HMAC the key before storing in Redis
   → Even if Redis is exposed, attacker can't forge keys
```

---

# 23. WebSockets & Real-time Features

## Simple Explanation

Normal HTTP is like sending a letter — you send request, wait for reply, connection closes. If server wants to tell you something, it can't — it has to wait for you to ask.

WebSocket is like a phone call — once connected, both sides can talk anytime. Server can push updates instantly without client asking.

## HTTP vs WebSocket

```
┌─────────────────────────────────────────────────────────────────┐
│                HTTP (Request-Response)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Client                    Server                                │
│    │                         │                                    │
│    │── GET /analytics ──────▶│  (open connection)                │
│    │◀── Response ────────────│  (close connection)               │
│    │                         │                                    │
│    │  ... 5 seconds later ...│                                    │
│    │── GET /analytics ──────▶│  (open connection again)          │
│    │◀── Response ────────────│  (close connection again)         │
│    │                         │                                    │
│    │  Problem: Polling every 5 sec = waste of bandwidth          │
│    │  Server can't notify client between polls                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                WEBSOCKET (Persistent Connection)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Client                    Server                                │
│    │                         │                                    │
│    │── Upgrade to WS ──────▶│  (connection stays OPEN)          │
│    │◀── Connected ───────────│                                    │
│    │                         │                                    │
│    │  ... Server detects new page view ...                       │
│    │◀── {"visitors": 42} ───│  (server pushes instantly!)       │
│    │                         │                                    │
│    │  ... Another view ...   │                                    │
│    │◀── {"visitors": 43} ───│  (again, instant!)                │
│    │                         │                                    │
│    │── {"type":"ping"} ────▶│  (client heartbeat)               │
│    │◀── {"type":"pong"} ────│                                    │
│    │                         │                                    │
│    │  Connection stays open for hours/days                       │
│    │  Zero overhead per message (no HTTP headers each time)      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Our WebSocket Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET ROOM SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────────────────────────────────────┐               │
│   │           CONNECTION MANAGER                  │               │
│   │                                               │               │
│   │  Room: "analytics"                           │               │
│   │    ├── Admin Browser Tab 1                   │               │
│   │    └── Admin Browser Tab 2                   │               │
│   │                                               │               │
│   │  Room: "notifications:user_5"                │               │
│   │    └── User 5's browser                      │               │
│   │                                               │               │
│   │  Room: "notifications:user_12"               │               │
│   │    ├── User 12's laptop browser              │               │
│   │    └── User 12's phone browser               │               │
│   │                                               │               │
│   │  Room: "admin"                               │               │
│   │    └── All admin connections                 │               │
│   └──────────────────────────────────────────────┘               │
│                                                                   │
│   OPERATIONS:                                                     │
│     broadcast("analytics", data)   → All in analytics room      │
│     send_to_user(user_id, data)    → All of that user's devices │
│     broadcast("admin", data)       → All admins                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Real-time Analytics Dashboard (What Admin Sees)

```
┌─────────────────────────────────────────────────────────────────┐
│ LIVE ANALYTICS DASHBOARD (updates without page refresh)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  When any visitor views a page:                                  │
│                                                                   │
│  Visitor's Browser           Backend              Admin Dashboard│
│       │                        │                        │         │
│       │ GET /projects          │                        │         │
│       │───────────────────────▶│                        │         │
│       │                        │ Record pageview        │         │
│       │                        │ in database            │         │
│       │                        │                        │         │
│       │                        │ Broadcast to           │         │
│       │                        │ "analytics" room:      │         │
│       │                        │───────────────────────▶│         │
│       │                        │ {                      │ Updates │
│       │                        │   "active_visitors":5, │ in      │
│       │                        │   "page": "/projects", │ real-   │
│       │                        │   "country": "India"   │ time!   │
│       │                        │ }                      │         │
│       │                        │                        │         │
│       │ 200 OK                 │                        │         │
│       │◀───────────────────────│                        │         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Heartbeat (Keep Alive)

```
WHY HEARTBEAT?
  WebSocket connections can silently die (user's WiFi drops, phone sleeps)
  Without heartbeat, server thinks connection is alive but it's dead
  = Memory leak (holding dead connections forever)

HOW:
  Every 30 seconds:
    Server → Client: {"type": "ping"}
    Client → Server: {"type": "pong"}   (within 10 seconds)
    
  If no pong received → connection is dead → clean up

LIKE: "Hello, you still there?" — "Haan bhai, I'm here" 
      If no reply → hang up the phone
```

---

# 24. Feature Flags & Progressive Rollouts

## Simple Explanation

You built a new dark mode feature. But you're not sure if it's bug-free. Do you release to ALL users at once and pray? No!

Feature Flags let you:
- Enable for only 10% users first (canary testing)
- Enable for only your team first (internal testing)
- Instantly disable if something breaks (kill switch)
- A/B test different versions

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   FEATURE FLAG SYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Admin Panel: "Feature Flags"                                   │
│   ┌─────────────────────────────────────────────────────┐       │
│   │ Flag Name         │ Status │ Rollout │ Targeting    │       │
│   ├───────────────────┼────────┼─────────┼──────────────┤       │
│   │ new_blog_editor   │ ✅ ON  │ 100%    │ All users    │       │
│   │ dark_mode_v2      │ ✅ ON  │ 25%     │ All users    │       │
│   │ ai_suggestions    │ ✅ ON  │ 100%    │ admin only   │       │
│   │ new_search_ui     │ ❌ OFF │ 0%      │ —            │       │
│   └───────────────────┴────────┴─────────┴──────────────┘       │
│                                                                   │
│   EVALUATION FLOW (when checking a flag):                        │
│                                                                   │
│   Is flag enabled? ──▶ NO → return false                        │
│         │                                                         │
│         ▼ YES                                                     │
│   Is user specifically targeted? ──▶ YES → return true          │
│         │                                                         │
│         ▼ NO                                                      │
│   Does user's role match? ──▶ YES → return true                 │
│         │                                                         │
│         ▼ NO                                                      │
│   Percentage rollout check:                                      │
│     hash(user_id + flag_name) % 100 < percentage?               │
│         │                    │                                    │
│         ▼ YES               ▼ NO                                 │
│     return true          return false                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Percentage Rollout — How It's Fair

```
PROBLEM: How to give exactly 25% of users the feature?
         And SAME users should always get same result (no flickering)!

SOLUTION: Deterministic hashing

  user_id = 42
  flag_name = "dark_mode_v2"
  
  hash = MD5("42:dark_mode_v2") = "a3f2..." → convert to number → 67
  
  percentage = 25
  
  Is 67 < 25? → NO → User 42 does NOT get dark_mode_v2
  
  user_id = 7
  hash = MD5("7:dark_mode_v2") = "1b8c..." → convert to number → 12
  
  Is 12 < 25? → YES → User 7 GETS dark_mode_v2

KEY POINTS:
  - Same user ALWAYS gets same hash → consistent experience
  - Different flag_name → different hash → different group
  - Increase percentage from 25% to 50% → user 42 (hash=67) still out
    But user with hash=30 who was out, now gets in
  - It's FAIR and DETERMINISTIC (not random each time)
```

## Practical Usage in Frontend

```javascript
// In React component:

function BlogEditor() {
  const { isEnabled } = useFeatureFlag("new_blog_editor");
  
  if (isEnabled) {
    return <NewFancyEditor />;      // New version
  }
  
  return <OldMarkdownEditor />;     // Safe fallback
}

// The flag evaluation happens:
// 1. On page load → fetch all flags for current user
// 2. Cache in memory (don't call API on every render)
// 3. Real-time update via WebSocket if admin changes flag
```

## Emergency Kill Switch

```
SCENARIO: You deployed "new_search_ui" to 100% users.
          Users report it's broken on mobile.

BEFORE FEATURE FLAGS:
  → Roll back deployment (takes 5-10 minutes)
  → All users affected during rollback
  → Stressful, might break other things

WITH FEATURE FLAGS:
  → Admin toggles "new_search_ui" to OFF
  → Takes 2 seconds
  → All users instantly get old search UI
  → Fix the bug calmly, test, then enable again
  → Zero downtime, zero stress
```

---

# 25. Content Versioning & Revision History

## Simple Explanation

Remember Google Docs? You can see "Version History" — who changed what and when. And you can restore any old version if you made a mistake.

We built the same for blog posts. Every time admin edits a blog, old version is saved. Can compare versions, see what changed, and roll back to any previous version.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTENT VERSIONING FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Blog Post: "How to Use React"                                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐         │
│  │ Revision History                                     │         │
│  ├─────────────────────────────────────────────────────┤         │
│  │ Rev 1 │ Jan 10 │ Initial version      │ 1200 words  │         │
│  │ Rev 2 │ Jan 12 │ Fixed typos          │ 1200 words  │         │
│  │ Rev 3 │ Jan 15 │ Added hooks section  │ 1800 words  │         │
│  │ Rev 4 │ Jan 20 │ Updated for React 19 │ 2100 words  │ ← live │
│  └─────────────────────────────────────────────────────┘         │
│                                                                   │
│  OPERATIONS:                                                      │
│                                                                   │
│  📋 View any revision → See exactly what was written then        │
│  🔍 Diff Rev 2 vs Rev 4 → See what changed (like git diff)      │
│  ⏪ Rollback to Rev 2 → Blog reverts to Jan 12 version           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Diff View (What Changed)

```
┌─────────────────────────────────────────────────────────────────┐
│  COMPARING: Revision 2 → Revision 3                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Title: "How to Use React" (unchanged)                           │
│                                                                   │
│  Content diff:                                                    │
│  ─────────────                                                    │
│    Line 45:                                                       │
│  - React 18 introduced concurrent features.                      │
│  + React 18 introduced concurrent features and Suspense.         │
│                                                                   │
│    Line 78: (NEW SECTION ADDED)                                  │
│  + ## Using Hooks Effectively                                    │
│  + Hooks are the modern way to manage state in React...          │
│  + useState, useEffect, useCallback, useMemo...                  │
│  + [600 words added]                                             │
│                                                                   │
│  STATS:                                                           │
│    Lines added: 42                                                │
│    Lines removed: 1                                               │
│    Lines changed: 1                                               │
│    Word count: 1200 → 1800 (+600)                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Non-Destructive Rollback

```
IMPORTANT: Rollback doesn't DELETE newer versions!

Before Rollback:
  Rev 1 → Rev 2 → Rev 3 → Rev 4 (current live)

Admin clicks: "Rollback to Rev 2"

After Rollback:
  Rev 1 → Rev 2 → Rev 3 → Rev 4 → Rev 5 (pre-rollback snapshot)
                                   → Rev 6 (rollback to Rev 2 content)
                                            ↑ (current live)

WHY NON-DESTRUCTIVE:
  - Rev 3, 4 are NOT deleted
  - Rev 5 saves current state before rollback (safety net)
  - Rev 6 is a new revision with Rev 2's content
  - You can even "rollback the rollback" if needed!
  
  Like: Git revert (not git reset --hard)
        Undo operation, not delete operation
```

## Database Model

```
┌────────────────────────────────────┐
│       blog_post_revisions          │
├────────────────────────────────────┤
│ id             │ Primary Key       │
│ post_id        │ FK → blog_posts   │
│ revision_number│ 1, 2, 3...       │
│ title          │ Title at that time│
│ content        │ Full content      │
│ excerpt        │ Excerpt           │
│ tags           │ Tags array        │
│ author_id      │ Who edited        │
│ change_summary │ "Fixed typos"     │
│ changed_fields │ ["content","tags"]│
│ word_count     │ Word count then   │
│ created_at     │ When revision made│
└────────────────────────────────────┘

API ENDPOINTS:
  GET  /blog/{id}/revisions           → List all revisions
  GET  /blog/{id}/revisions/{rev}     → Get specific revision
  GET  /blog/{id}/revisions/2/diff/4  → Compare rev 2 vs rev 4
  POST /blog/{id}/revisions/2/rollback → Rollback to rev 2
```

---

# 26. Observability: Logging, Metrics & Tracing

## Simple Explanation

Imagine running a restaurant. You need to know:
- **Logging**: What happened? (Order #45 was served, customer complained)
- **Metrics**: How are we doing overall? (Average wait time 12 min, 95% happy)
- **Tracing**: What went wrong with THIS order? (Cook was slow + waiter dropped it)

Same in software — without observability, you're running blind.

## The Three Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│              THREE PILLARS OF OBSERVABILITY                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │   LOGGING    │  │   METRICS    │  │    TRACING       │      │
│  │              │  │              │  │                  │      │
│  │ What happened│  │ How much/    │  │ Why this request │      │
│  │ (events)    │  │ how fast     │  │ was slow         │      │
│  │              │  │ (numbers)    │  │ (journey map)    │      │
│  │              │  │              │  │                  │      │
│  │ "User 5     │  │ Requests/sec:│  │ Request abc123:  │      │
│  │  logged in  │  │  250         │  │ → Auth: 5ms      │      │
│  │  from Mumbai│  │              │  │ → DB query: 45ms │      │
│  │  at 2:30PM" │  │ Error rate:  │  │ → Redis: 2ms     │      │
│  │              │  │  0.1%        │  │ → Response: 52ms │      │
│  │ "Project    │  │              │  │                  │      │
│  │  creation   │  │ P99 latency: │  │ (Spans show each │      │
│  │  failed:    │  │  180ms       │  │  step's time)    │      │
│  │  DB timeout"│  │              │  │                  │      │
│  └──────────────┘  └──────────────┘  └──────────────────┘      │
│                                                                   │
│  TOOLS WE USE:                                                    │
│  structlog        Prometheus         OpenTelemetry                │
│  (JSON logs)      (time-series DB)   (distributed tracing)       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Structured Logging (Not Just print())

```
BAD LOGGING (what beginners do):
  print("user logged in")
  print("error occurred")
  print(f"project created: {project_id}")

PROBLEMS:
  - Can't search/filter logs (which user? when? what error?)
  - No context (what was the request? which server?)
  - No severity levels (is this critical or informational?)

GOOD LOGGING (structured with context):
  {
    "timestamp": "2024-01-15T14:30:00Z",
    "level": "info",
    "event": "user.login.success",
    "user_id": 5,
    "email": "user@example.com",
    "ip": "103.x.x.x",
    "user_agent": "Chrome/120",
    "request_id": "req_abc123",
    "duration_ms": 45
  }

NOW YOU CAN:
  - Filter: show me all errors in last 1 hour
  - Search: show me all actions by user_id=5
  - Correlate: show me everything about request "req_abc123"
  - Alert: if error rate > 5%, send Slack notification
```

## Request ID Correlation

```
┌─────────────────────────────────────────────────────────────────┐
│              REQUEST ID — THE DETECTIVE'S TOOL                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Every request gets a unique ID (like Aadhaar for requests)      │
│                                                                   │
│  Request comes in → Generate: "req_7f3a2b9c"                    │
│                                                                   │
│  ALL logs for this request include this ID:                      │
│                                                                   │
│  [req_7f3a2b9c] → Received POST /projects                       │
│  [req_7f3a2b9c] → Auth: token valid, user=admin                 │
│  [req_7f3a2b9c] → Validation: passed                            │
│  [req_7f3a2b9c] → DB: INSERT project (45ms)                     │
│  [req_7f3a2b9c] → Cache: invalidated projects:*                 │
│  [req_7f3a2b9c] → Event: ProjectCreated published               │
│  [req_7f3a2b9c] → Response: 201 Created (67ms total)            │
│                                                                   │
│  Response includes: X-Request-ID: req_7f3a2b9c                  │
│                                                                   │
│  When user reports bug: "I got error, request ID is req_7f3a2b9c"│
│  You search logs by this ID → see EXACTLY what happened!         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Prometheus Metrics

```
WHAT PROMETHEUS DOES:
  Collects numbers over time. Like fitness tracker for your app.

METRICS WE TRACK:

1. REQUEST COUNTER (how many requests total):
   http_requests_total{method="GET", endpoint="/projects", status="200"} = 45231
   http_requests_total{method="POST", endpoint="/auth/login", status="401"} = 89

2. LATENCY HISTOGRAM (how fast are responses):
   http_request_duration_seconds{endpoint="/projects"}
     p50 = 0.045  (50% of requests under 45ms — median)
     p90 = 0.120  (90% under 120ms — most users)
     p99 = 0.350  (99% under 350ms — worst case)

3. ACTIVE CONNECTIONS GAUGE (right now):
   active_websocket_connections = 3
   active_http_requests = 12
   database_pool_used = 4

4. ERROR RATE:
   (http_requests_total{status="500"} / http_requests_total) × 100 = 0.02%

DASHBOARDS (Grafana — free):
  ┌─────────────────────────────────────────┐
  │ 📈 Requests/sec: 45    Errors: 0.02%   │
  │ ⏱️ P99 Latency: 180ms  Uptime: 99.9%   │
  │ 👥 Active Users: 12    WS Conn: 3      │
  └─────────────────────────────────────────┘
```

---

# 27. PWA, Service Workers & Offline Support

## Simple Explanation

PWA (Progressive Web App) means your website can work like a mobile app:
- Install on home screen (no Play Store needed)
- Works offline (cached pages still visible)
- Push notifications (like WhatsApp)
- Fast loading (assets cached locally)

## How Service Worker Works

```
┌─────────────────────────────────────────────────────────────────┐
│              SERVICE WORKER — THE MIDDLEMAN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Without Service Worker:                                         │
│    Browser ────────── Internet ────────── Server                 │
│    (If internet down, nothing works)                             │
│                                                                   │
│  With Service Worker:                                            │
│    Browser ──── Service Worker ──── Internet ──── Server         │
│                      │                                            │
│                      │ Has local cache!                           │
│                      │ Can respond WITHOUT internet!             │
│                      ▼                                            │
│                 ┌──────────┐                                     │
│                 │  CACHE   │                                     │
│                 │  ------  │                                     │
│                 │  HTML    │                                     │
│                 │  CSS     │                                     │
│                 │  JS      │                                     │
│                 │  Images  │                                     │
│                 │  API data│                                     │
│                 └──────────┘                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Caching Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│ STRATEGY 1: CACHE FIRST (for static assets — CSS, JS, images)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request: GET /styles.css                                        │
│    1. Check cache → Found? → Return from cache (instant!)       │
│    2. Not in cache? → Fetch from network → Store in cache        │
│                                                                   │
│  Best for: Files that rarely change (fonts, icons, bundled JS)   │
│  Result: After first visit, everything loads INSTANTLY           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STRATEGY 2: NETWORK FIRST (for API calls — fresh data)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request: GET /api/projects                                      │
│    1. Try network first → Success? → Return & update cache      │
│    2. Network failed? → Return from cache (stale but better     │
│       than nothing!)                                             │
│                                                                   │
│  Best for: API data that changes often but has acceptable stale  │
│  Result: Always tries fresh data, falls back to cached if offline│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STRATEGY 3: STALE WHILE REVALIDATE (for ISR pages)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request: GET /blog/my-post                                      │
│    1. Return cached version IMMEDIATELY (fast!)                  │
│    2. In background: fetch fresh version from network            │
│    3. Update cache for next time                                 │
│                                                                   │
│  Best for: Content that's not time-critical (blogs, projects)    │
│  Result: Instant load + eventually fresh content                 │
└─────────────────────────────────────────────────────────────────┘
```

## Background Sync (Offline Forms)

```
SCENARIO: User fills contact form but WiFi drops when they submit

WITHOUT Background Sync:
  → Error: "Network failed" → User loses their message → Frustration!

WITH Background Sync:
  → Form saved locally
  → "Message saved! Will send when you're back online."
  → WiFi comes back
  → Service Worker auto-sends the saved message
  → User gets notification: "Your message was sent!" ✓

HOW:
  1. Contact form submit → navigator.serviceWorker.ready
  2. Register sync event: sync.register("contact-form-sync")
  3. Store form data in IndexedDB
  4. When online → sync event fires → send stored data → clear IndexedDB
```

## PWA Manifest (Install as App)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PWA INSTALL EXPERIENCE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User visits your portfolio on phone Chrome:                     │
│                                                                   │
│  ┌─────────────────────────┐                                    │
│  │ ┌─────────────────────┐ │                                    │
│  │ │                     │ │                                    │
│  │ │   Your Portfolio    │ │                                    │
│  │ │                     │ │                                    │
│  │ │ ─────────────────── │ │                                    │
│  │ │ Add to Home Screen? │ │  ← Browser shows install prompt   │
│  │ │   [Install]  [No]   │ │                                    │
│  │ │                     │ │                                    │
│  │ └─────────────────────┘ │                                    │
│  └─────────────────────────┘                                    │
│                                                                   │
│  After install:                                                   │
│  - App icon on home screen (with your logo)                      │
│  - Opens in standalone mode (no browser chrome)                  │
│  - Splash screen with your branding                              │
│  - Works offline (cached content visible)                        │
│  - Push notifications work                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

# 28. Full-Text Search & Autocomplete

## Simple Explanation

When you type "react hooks" in search:
- **Basic search**: LIKE '%react hooks%' → only finds exact match in that order
- **Full-text search**: Finds "Using React's Custom Hooks", "Hooks in React 19", even "ReactJS hook patterns" → understands language!

PostgreSQL has built-in full-text search — no need for Elasticsearch (saves ₹0 vs ₹3000/month).

## How Full-Text Search Works

```
┌─────────────────────────────────────────────────────────────────┐
│            FULL-TEXT SEARCH PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INDEXING (when project/blog is created):                        │
│                                                                   │
│  Title: "Building REST APIs with FastAPI and Python"             │
│         │                                                         │
│         ▼  Step 1: Tokenize (split into words)                   │
│  ["Building", "REST", "APIs", "with", "FastAPI", "and", "Python"]│
│         │                                                         │
│         ▼  Step 2: Remove stop words (useless words)             │
│  ["Building", "REST", "APIs", "FastAPI", "Python"]               │
│         │                                                         │
│         ▼  Step 3: Stem (reduce to root form)                    │
│  ["build", "rest", "api", "fastapi", "python"]                   │
│         │                                                         │
│         ▼  Step 4: Store as tsvector (searchable format)         │
│  'api':3 'build':1 'fastapi':4 'python':5 'rest':2              │
│  (word:position format — used for ranking)                       │
│                                                                   │
│                                                                   │
│  SEARCHING (when user searches):                                 │
│                                                                   │
│  Query: "python api"                                             │
│         │                                                         │
│         ▼  Convert to tsquery                                    │
│  'python' & 'api'   (both words must be present)                │
│         │                                                         │
│         ▼  Match against tsvector                                │
│  Title "Building REST APIs with FastAPI and Python"              │
│    → Has 'api'? ✓  Has 'python'? ✓  → MATCH! Rank: 0.8        │
│                                                                   │
│  Title "React Component Patterns"                                │
│    → Has 'api'? ✗  → NO MATCH                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Search Ranking (Best Result First)

```
HOW RANKING WORKS (ts_rank_cd):

  We assign WEIGHTS to different fields:
    Title    → Weight A (highest — most important)
    Tags     → Weight B (medium — good signal)
    Content  → Weight C (lowest — lots of text, less specific)

  Example search: "react hooks"
  
  Result 1: Title="React Hooks Guide" → word in title → high rank (0.9)
  Result 2: Title="JS Patterns" content has "react hooks" → lower rank (0.3)
  
  Results sorted by rank → most relevant first!
  
  LIKE: Google search. Title match > URL match > body text match.
```

## Autocomplete (Type-Ahead)

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOCOMPLETE FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User types: "rea"                                               │
│                                                                   │
│  ┌──────────────────────────────────┐                           │
│  │ 🔍 rea                           │                           │
│  ├──────────────────────────────────┤                           │
│  │ → React Hooks Deep Dive          │  (title starts with "rea")│
│  │ → Real-time Chat with WebSockets │                           │
│  │ → Reactive Programming in Python │                           │
│  └──────────────────────────────────┘                           │
│                                                                   │
│  HOW:                                                            │
│    SQL: SELECT title FROM projects                               │
│         WHERE title ILIKE 'rea%'                                 │
│         LIMIT 5                                                   │
│                                                                   │
│  Fast because: GIN index on title with gin_trgm_ops             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Fuzzy Search (Typo Tolerance)

```
USER TYPES: "reakt" (typo — meant "react")

WITHOUT FUZZY: No results. User confused.

WITH FUZZY (Trigram Similarity):
  "reakt" vs "react" → similarity = 0.6 (threshold: 0.2)
  → Shows results for "react" anyway!

HOW TRIGRAMS WORK:
  "react" → {"  r", " re", "rea", "eac", "act", "ct "}
  "reakt" → {"  r", " re", "rea", "eak", "akt", "kt "}
  
  Common trigrams: {"  r", " re", "rea"} = 3 out of 6
  Similarity: 3/6 = 0.5 → above 0.2 threshold → MATCH!

REQUIRES: pg_trgm extension (we enabled it in migration)
```

---

# 29. Graceful Shutdown & Zero-Downtime Deploys

## Simple Explanation

Your app is serving 50 users right now. You need to deploy a new version. What happens to those 50 users' requests?

**Without graceful shutdown**: Kill process → 50 users get "Connection Reset" errors. Half-written database transactions might corrupt data.

**With graceful shutdown**: Stop accepting NEW requests → Let current 50 requests finish → Then shut down. Nobody notices anything.

## The 5-Phase Shutdown Process

```
┌─────────────────────────────────────────────────────────────────┐
│               GRACEFUL SHUTDOWN (5 Phases)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SIGTERM received (Railway/Docker says "time to stop")           │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Phase 1: STOP ACCEPTING (immediate)                  │        │
│  │                                                       │        │
│  │ • Health check returns 503 (load balancer removes us) │        │
│  │ • New connections refused                             │        │
│  │ • Existing connections continue                       │        │
│  └────────────────────────────────────────┬──────────────┘        │
│                                           │                       │
│       ▼                                   │ max 30 seconds        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Phase 2: DRAIN HTTP REQUESTS                         │        │
│  │                                                       │        │
│  │ • Wait for all in-flight HTTP requests to complete   │        │
│  │ • Counter: active_requests tracks them               │        │
│  │ • Each request finishing → counter decrements        │        │
│  │ • When counter = 0 → move to Phase 3                 │        │
│  └────────────────────────────────────────┬──────────────┘        │
│                                           │                       │
│       ▼                                   │ max 10 seconds        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Phase 3: DRAIN WEBSOCKET CONNECTIONS                  │        │
│  │                                                       │        │
│  │ • Send "server shutting down" to all WS clients      │        │
│  │ • Close connections gracefully (1000 code)           │        │
│  │ • Clients auto-reconnect to new server instance      │        │
│  └────────────────────────────────────────┬──────────────┘        │
│                                           │                       │
│       ▼                                   │ max 15 seconds        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Phase 4: DRAIN BACKGROUND TASKS                      │        │
│  │                                                       │        │
│  │ • Wait for running background jobs to finish         │        │
│  │ • New jobs NOT picked up (other workers handle them) │        │
│  │ • Email sending, GitHub sync, etc. complete first    │        │
│  └────────────────────────────────────────┬──────────────┘        │
│                                           │                       │
│       ▼                                   │                       │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Phase 5: EXECUTE SHUTDOWN HOOKS (in priority order)   │        │
│  │                                                       │        │
│  │ Priority 100: Close database connections              │        │
│  │ Priority 90:  Close Redis connections                 │        │
│  │ Priority 80:  Flush log buffers                      │        │
│  │ Priority 70:  Send final metrics                     │        │
│  │                                                       │        │
│  │ All resources properly released. No leaks!           │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                   │
│  Process exits cleanly (exit code 0)                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Zero-Downtime Deployment (How Railway Does It)

```
┌─────────────────────────────────────────────────────────────────┐
│            ZERO-DOWNTIME DEPLOY FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  BEFORE DEPLOY:                                                   │
│    Load Balancer → [Server v1 (running)] ← all traffic          │
│                                                                   │
│  STEP 1: Start new version                                       │
│    Load Balancer → [Server v1 (running)] ← traffic continues    │
│                    [Server v2 (starting)]                         │
│                                                                   │
│  STEP 2: Health check passes on v2                               │
│    Load Balancer → [Server v1 (running)] ← old traffic          │
│                 ↘  [Server v2 (healthy)] ← new traffic starts   │
│                                                                   │
│  STEP 3: Send SIGTERM to v1                                      │
│    Load Balancer → [Server v1 (draining)] ← finishing old reqs  │
│                 ↘  [Server v2 (healthy)] ← all new traffic      │
│                                                                   │
│  STEP 4: v1 finishes graceful shutdown                           │
│    Load Balancer → [Server v2 (healthy)] ← all traffic          │
│                    [Server v1 (stopped)] → removed               │
│                                                                   │
│  RESULT: Not a single user saw an error!                         │
│          Old requests completed on v1                             │
│          New requests handled by v2                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Signal Handling

```
WHAT ARE SIGNALS?
  Operating system's way to talk to processes.
  Like tapping someone on the shoulder.

SIGTERM (signal 15):
  "Please shut down gracefully"
  Railway/Docker sends this first
  Our app: starts graceful shutdown

SIGINT (signal 2):
  "Ctrl+C pressed" (in development)
  Our app: same graceful shutdown

SIGKILL (signal 9):
  "DIE NOW" (force kill — cannot be caught)
  Railway sends this if SIGTERM takes too long (>30 sec)
  Our app: can't handle this — process just dies
  
  That's why we have timeout on each phase!
  Total: 30 + 10 + 15 = 55 seconds (but Railway gives 30)
  So we keep each phase short.
```

---

# Conclusion

## What You've Built (The Complete Picture)

```
┌─────────────────────────────────────────────────────────────────┐
│                COMPLETE ARCHITECTURE OVERVIEW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─── FRONTEND (Vercel) ────────────────────────────────────┐   │
│  │ Next.js 14 │ TypeScript │ Tailwind │ Framer Motion       │   │
│  │ PWA + Service Worker │ ISR │ React Query │ Zustand       │   │
│  │ Error Boundaries │ Optimistic UI │ Web Vitals            │   │
│  │ Playwright E2E │ Lighthouse CI │ WCAG 2.1 AA            │   │
│  └───────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌─── BACKEND (Railway) ────────────────────────────────────┐   │
│  │ FastAPI │ SQLAlchemy Async │ Pydantic │ JWT + OAuth       │   │
│  │ Circuit Breaker │ Token Bucket │ Idempotency Keys        │   │
│  │ Event Bus │ Feature Flags │ WebSockets                   │   │
│  │ Full-Text Search │ Content Versioning │ Cursor Pagination│   │
│  │ Graceful Shutdown │ Structured Logging │ Prometheus      │   │
│  │ ARQ Job Queue │ Redis Caching │ Alembic Migrations       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌─── DATA LAYER ───────────────────────────────────────────┐   │
│  │ PostgreSQL (Supabase) │ Redis (Upstash) │ GIN Indexes    │   │
│  │ Full-Text Vectors │ Trigram Search │ Composite Indexes   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─── DEVOPS ───────────────────────────────────────────────┐   │
│  │ GitHub Actions CI/CD │ Docker │ Sentry │ UptimeRobot     │   │
│  │ Dependabot │ Lighthouse Performance Budgets              │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## MNC Interview Topics Covered

| Topic | Where in This Project | Companies That Ask |
|-------|----------------------|-------------------|
| System Design | Full architecture | All MNCs |
| API Design | REST + WebSocket + OpenAPI | Google, Microsoft |
| Authentication | JWT + OAuth + Token Rotation | All MNCs |
| Database Design | Normalization + Indexing + Migrations | Amazon, Flipkart |
| Caching | Redis + Cache-Aside + ETags | Netflix, Uber |
| Rate Limiting | Token Bucket + Per-endpoint | Stripe, Razorpay |
| Search | Full-Text + Autocomplete + Fuzzy | Google, Swiggy |
| Real-time | WebSockets + Event Bus | Slack, Discord |
| Resilience | Circuit Breaker + Graceful Shutdown | Netflix, Amazon |
| Observability | Logging + Metrics + Tracing | All MNCs |
| Testing | Unit + E2E + Accessibility | All MNCs |
| CI/CD | GitHub Actions + Docker | All MNCs |
| Security | CORS + CSP + HSTS + Input Sanitization | All MNCs |
| Performance | Lighthouse 95+ + ISR + PWA | Google, Vercel |
| Feature Flags | Progressive Rollout + A/B | Netflix, Microsoft |
| Idempotency | Safe Retries + Deduplication | Stripe, Razorpay |
| Pagination | Cursor-based + Keyset | Facebook, Twitter |
| Content Management | Versioning + Diff + Rollback | WordPress, Medium |

## How To Explain This In Interviews

```
WHEN THEY ASK: "Tell me about a complex project you built"

YOUR ANSWER STRUCTURE:
1. High level: "Full-stack portfolio with enterprise patterns"
2. Pick 2-3 interesting patterns: "I implemented circuit breaker because..."
3. Explain the PROBLEM you solved: "Without it, one service down = entire app down"
4. Show the TRADE-OFF: "I chose token bucket over sliding window because..."
5. Mention testing: "I have 55+ unit tests and E2E tests with Playwright"

WHEN THEY ASK: "How would you handle X at scale?"
→ Point to your actual implementation. You HAVE done it!

WHEN THEY ASK: "What's your approach to system design?"
→ Walk through your architecture. Explain each layer's responsibility.
→ Mention observability, resilience, security as cross-cutting concerns.
```

## Final Numbers

```
CODEBASE STATS:
  Backend:    ~4000 lines of Python
  Frontend:   ~3500 lines of TypeScript/React
  Tests:      55+ test cases
  API Docs:   Auto-generated OpenAPI (Swagger + ReDoc)
  Book:       This document (29 chapters)
  
FEATURES:
  Core:       Auth, CRUD, Blog, Contact, Analytics, Admin
  Advanced:   12 production-grade patterns
  DevOps:     CI/CD, Docker, Monitoring, Deployment docs
  
COST:
  Hosting:    ₹0/month (all free tier)
  Domain:     ₹500/year (optional)
  Total:      Less than a pizza 🍕
```

---

*Built with: FastAPI + Next.js 14 + PostgreSQL + Redis + TypeScript*
*Patterns: Circuit Breaker + Event Bus + Token Bucket + Cursor Pagination + Idempotency + WebSockets + Feature Flags + Content Versioning + Observability + PWA + Full-Text Search + Graceful Shutdown*
*Deployed on: Vercel + Railway + Supabase (all free tier)*
*Security: JWT + OAuth + Rate Limiting + CSP + CORS + HMAC + Idempotency*
*Performance: Lighthouse 95+ | TTFB < 200ms | PWA Offline | WCAG 2.1 AA*
