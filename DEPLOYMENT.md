# Deployment Guide

Complete deployment instructions for Vercel (frontend), Railway (backend), and Supabase (database).

---

## Prerequisites

- GitHub repository with the project pushed
- Accounts on: [Vercel](https://vercel.com), [Railway](https://railway.app), [Supabase](https://supabase.com), [Upstash](https://upstash.com)
- All accounts have free tiers sufficient for this project

---

## 1. Supabase (PostgreSQL Database)

### Setup

1. Go to [supabase.com](https://supabase.com) → New Project
2. Choose a region close to your Railway deployment
3. Set a strong database password (save it!)
4. Wait for project to initialize (~2 minutes)

### Get Connection String

1. Go to **Settings → Database**
2. Copy the **Connection string (URI)** under "Connection pooling"
3. Format: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
4. For async SQLAlchemy, change the scheme:
   ```
   postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

### Run Migrations

After deploying the backend, run:
```bash
# From your local machine with DATABASE_URL pointing to Supabase
cd backend
alembic upgrade head
```

Or create an initial migration first:
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## 2. Upstash (Redis)

### Setup

1. Go to [upstash.com](https://upstash.com) → Create Database
2. Choose the same region as Supabase
3. Select **Free tier** (10,000 commands/day)
4. Copy the **Redis URL** (starts with `rediss://`)

### Configuration

The URL format is: `rediss://default:[password]@[endpoint]:6379`

Note: Upstash uses `rediss://` (with SSL) not `redis://`

---

## 3. Railway (Backend - FastAPI)

### Setup

1. Go to [railway.app](https://railway.app) → New Project
2. Choose **Deploy from GitHub repo**
3. Select your repository
4. Railway auto-detects the Dockerfile in `backend/`

### Configure Service

1. **Root Directory**: Set to `backend`
2. **Build Command**: Railway will use the Dockerfile automatically
3. **Port**: Railway assigns this via `PORT` env var (already handled in Dockerfile)

### Environment Variables

Set these in Railway's dashboard → Variables:

```env
# Database (from Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Redis (from Upstash)
REDIS_URL=rediss://default:[password]@[endpoint]:6379

# Application
SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_hex(32))">
ENVIRONMENT=production
DEBUG=false

# CORS (your Vercel domain)
CORS_ORIGINS=https://your-portfolio.vercel.app

# Email (use Gmail App Password or any SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
ADMIN_EMAIL=your-email@gmail.com

# GitHub API
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=ghp_your_token

# OAuth (optional)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=https://your-api.railway.app/api/v1/auth/github/callback
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://your-api.railway.app/api/v1/auth/google/callback

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5
CONTACT_RATE_LIMIT_PER_HOUR=3
```

### Custom Domain (Optional)

1. Railway provides a `*.railway.app` domain automatically
2. For custom domain: Settings → Domains → Add Custom Domain
3. Add CNAME record at your DNS provider

### Health Check

Configure Railway health check: `GET /health`

---

## 4. Vercel (Frontend - Next.js)

### Setup

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repository
3. **Framework Preset**: Next.js (auto-detected)
4. **Root Directory**: Set to `frontend`

### Environment Variables

Set in Vercel Dashboard → Settings → Environment Variables:

```env
NEXT_PUBLIC_API_URL=https://your-api.railway.app
```

### Build Settings

- **Build Command**: `npm run build` (default)
- **Output Directory**: `.next` (default)
- **Install Command**: `npm ci` (default)

### Custom Domain (Optional)

1. Vercel provides `*.vercel.app` domain
2. For custom: Settings → Domains → Add
3. Update DNS records as instructed

---

## 5. GitHub OAuth Setup

### Create GitHub OAuth App

1. Go to GitHub → Settings → Developer Settings → OAuth Apps → New
2. **Application name**: Your Portfolio
3. **Homepage URL**: `https://your-portfolio.vercel.app`
4. **Authorization callback URL**: `https://your-api.railway.app/api/v1/auth/github/callback`
5. Copy Client ID and generate Client Secret
6. Add to Railway env vars

### Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Add authorized redirect URI: `https://your-api.railway.app/api/v1/auth/google/callback`
5. Copy Client ID and Secret → add to Railway env vars

---

## 6. GitHub Actions Secrets

For CI/CD to work, add these secrets to your GitHub repo (Settings → Secrets → Actions):

```
RAILWAY_TOKEN=<from Railway dashboard → Account → Tokens>
VERCEL_TOKEN=<from Vercel dashboard → Account → Tokens>
VERCEL_ORG_ID=<from Vercel project settings>
VERCEL_PROJECT_ID=<from Vercel project settings>
```

---

## 7. Post-Deployment Checklist

- [ ] Run database migrations: `alembic upgrade head`
- [ ] Create admin user (signup via API, then update role in Supabase SQL editor):
  ```sql
  UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
  ```
- [ ] Verify health check: `curl https://your-api.railway.app/health`
- [ ] Test frontend loads: Visit `https://your-portfolio.vercel.app`
- [ ] Test login flow end-to-end
- [ ] Verify CORS (frontend can reach API)
- [ ] Check rate limiting is working
- [ ] Submit a test contact form
- [ ] Verify GitHub integration shows repos

---

## 8. Monitoring & Maintenance

### Sentry (Optional, Free Tier)

1. Create project at [sentry.io](https://sentry.io)
2. Add DSN to Railway env: `SENTRY_DSN=https://...@sentry.io/...`
3. Errors will be tracked automatically (SDK already in requirements)

### Database Backups

Supabase handles automated daily backups on Pro plan. On free tier:
- Use `pg_dump` periodically for manual backups
- Or enable Supabase's point-in-time recovery (paid)

### Scaling Notes

| Service | Free Tier Limit | Upgrade Trigger |
|---------|----------------|-----------------|
| Vercel | 100GB bandwidth/mo | High traffic |
| Railway | $5 credit/mo | Sustained uptime |
| Supabase | 500MB DB, 1GB transfer | Data growth |
| Upstash | 10K commands/day | High analytics traffic |

---

## Troubleshooting

### Common Issues

**CORS errors**: Ensure `CORS_ORIGINS` in Railway matches your Vercel domain exactly (with `https://`, no trailing slash).

**Database connection failures**: Check the connection string uses `postgresql+asyncpg://` scheme and connection pooling is enabled in Supabase.

**Redis connection refused**: Upstash uses TLS (`rediss://`). Ensure the URL starts with `rediss://` not `redis://`.

**Build fails on Vercel**: Check that `NEXT_PUBLIC_API_URL` is set. The `next.config.js` references it.

**Railway deploy fails**: Ensure the root directory is set to `backend` and the Dockerfile is valid.
