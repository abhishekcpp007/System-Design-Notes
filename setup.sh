#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════╗
# ║          PORTFOLIO PROJECT - ONE-TIME SETUP SCRIPT                  ║
# ║                                                                      ║
# ║  This script will ask you all the required information and          ║
# ║  automatically create your .env files so the project runs directly. ║
# ╚══════════════════════════════════════════════════════════════════════╝

set -e

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       🚀 PORTFOLIO PROJECT SETUP WIZARD                     ║${NC}"
echo -e "${CYAN}║       Fill all placeholders with your real data             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─────────────────────────────────────────────────
# SECTION 1: BASIC INFO
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 1: YOUR BASIC INFORMATION${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

read -p "$(echo -e ${GREEN}Your Full Name ${NC}[e.g., Rahul Sharma]: )" FULL_NAME
read -p "$(echo -e ${GREEN}Your Email ${NC}[e.g., rahul@gmail.com]: )" ADMIN_EMAIL
read -p "$(echo -e ${GREEN}Your GitHub Username ${NC}[e.g., rahulsharma]: )" GITHUB_USERNAME
read -p "$(echo -e ${GREEN}Your Domain ${NC}[leave blank for localhost, e.g., rahul.dev]: )" DOMAIN

# Set defaults
if [ -z "$DOMAIN" ]; then
    FRONTEND_URL="http://localhost:3000"
    BACKEND_URL="http://localhost:8000"
    CORS_ORIGINS="http://localhost:3000"
else
    FRONTEND_URL="https://${DOMAIN}"
    BACKEND_URL="https://api.${DOMAIN}"
    CORS_ORIGINS="http://localhost:3000,https://${DOMAIN}"
fi

echo ""

# ─────────────────────────────────────────────────
# SECTION 2: DATABASE (Choose local or Supabase)
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 2: DATABASE SETUP${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Choose database option:${NC}"
echo "  1) Local PostgreSQL (via Docker - recommended for development)"
echo "  2) Supabase (cloud - for production/deployment)"
echo ""
read -p "$(echo -e ${GREEN}Enter 1 or 2: ${NC})" DB_CHOICE

if [ "$DB_CHOICE" == "2" ]; then
    echo ""
    echo -e "${YELLOW}Go to https://supabase.com → Create project → Settings → Database → Connection String${NC}"
    echo -e "${YELLOW}Copy the URI and replace [YOUR-PASSWORD] with your DB password${NC}"
    echo -e "${YELLOW}Change 'postgresql://' to 'postgresql+asyncpg://' at the start${NC}"
    echo ""
    read -p "$(echo -e ${GREEN}Supabase Database URL: ${NC})" DATABASE_URL
else
    DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio"
    echo -e "${GREEN}Using local Docker PostgreSQL ✓${NC}"
fi

echo ""

# ─────────────────────────────────────────────────
# SECTION 3: REDIS (Choose local or Upstash)
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 3: REDIS SETUP${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Choose Redis option:${NC}"
echo "  1) Local Redis (via Docker - recommended for development)"
echo "  2) Upstash (cloud - for production/deployment)"
echo ""
read -p "$(echo -e ${GREEN}Enter 1 or 2: ${NC})" REDIS_CHOICE

if [ "$REDIS_CHOICE" == "2" ]; then
    echo ""
    echo -e "${YELLOW}Go to https://upstash.com → Create Redis Database → Copy the Redis URL${NC}"
    echo -e "${YELLOW}Format: rediss://default:password@hostname:6379${NC}"
    echo ""
    read -p "$(echo -e ${GREEN}Upstash Redis URL: ${NC})" REDIS_URL
else
    REDIS_URL="redis://localhost:6379"
    echo -e "${GREEN}Using local Docker Redis ✓${NC}"
fi

echo ""

# ─────────────────────────────────────────────────
# SECTION 4: GITHUB API (for portfolio stats)
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 4: GITHUB API TOKEN${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}This shows your GitHub repos, languages, and contribution stats on portfolio.${NC}"
echo -e "${YELLOW}Create token: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)${NC}"
echo -e "${YELLOW}Scopes needed: 'read:user' and 'public_repo'${NC}"
echo -e "${YELLOW}(Leave blank to skip - GitHub section will show placeholder data)${NC}"
echo ""
read -p "$(echo -e ${GREEN}GitHub Personal Access Token ${NC}[ghp_xxxxx]: )" GITHUB_TOKEN

echo ""

# ─────────────────────────────────────────────────
# SECTION 5: OAUTH (Optional — for social login)
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 5: OAUTH SETUP (Optional - for social login)${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Skip this if you just want email/password login for now.${NC}"
echo ""
read -p "$(echo -e ${GREEN}Setup GitHub OAuth? ${NC}[y/N]: )" SETUP_GITHUB_OAUTH

if [ "$SETUP_GITHUB_OAUTH" == "y" ] || [ "$SETUP_GITHUB_OAUTH" == "Y" ]; then
    echo ""
    echo -e "${YELLOW}Create: GitHub → Settings → Developer settings → OAuth Apps → New OAuth App${NC}"
    echo -e "${YELLOW}Homepage URL: ${FRONTEND_URL}${NC}"
    echo -e "${YELLOW}Callback URL: ${FRONTEND_URL}/auth/callback${NC}"
    echo ""
    read -p "$(echo -e ${GREEN}GitHub OAuth Client ID: ${NC})" GITHUB_CLIENT_ID
    read -p "$(echo -e ${GREEN}GitHub OAuth Client Secret: ${NC})" GITHUB_CLIENT_SECRET
    GITHUB_REDIRECT_URI="${FRONTEND_URL}/auth/callback"
else
    GITHUB_CLIENT_ID=""
    GITHUB_CLIENT_SECRET=""
    GITHUB_REDIRECT_URI=""
fi

echo ""
read -p "$(echo -e ${GREEN}Setup Google OAuth? ${NC}[y/N]: )" SETUP_GOOGLE_OAUTH

if [ "$SETUP_GOOGLE_OAUTH" == "y" ] || [ "$SETUP_GOOGLE_OAUTH" == "Y" ]; then
    echo ""
    echo -e "${YELLOW}Create: Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID${NC}"
    echo -e "${YELLOW}Authorized redirect URI: ${FRONTEND_URL}/auth/callback${NC}"
    echo ""
    read -p "$(echo -e ${GREEN}Google OAuth Client ID: ${NC})" GOOGLE_CLIENT_ID
    read -p "$(echo -e ${GREEN}Google OAuth Client Secret: ${NC})" GOOGLE_CLIENT_SECRET
    GOOGLE_REDIRECT_URI="${FRONTEND_URL}/auth/callback"
else
    GOOGLE_CLIENT_ID=""
    GOOGLE_CLIENT_SECRET=""
    GOOGLE_REDIRECT_URI=""
fi

echo ""

# ─────────────────────────────────────────────────
# SECTION 6: EMAIL (Optional — for contact form)
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 6: EMAIL SETUP (Optional - for contact form notifications)${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}This sends you email when someone submits contact form.${NC}"
echo -e "${YELLOW}You can use Gmail SMTP (free) or any SMTP provider.${NC}"
echo -e "${YELLOW}For Gmail: Enable 2FA → Create App Password → Use that as SMTP_PASSWORD${NC}"
echo -e "${YELLOW}Skip this if you don't need email notifications yet.${NC}"
echo ""
read -p "$(echo -e ${GREEN}Setup Email? ${NC}[y/N]: )" SETUP_EMAIL

if [ "$SETUP_EMAIL" == "y" ] || [ "$SETUP_EMAIL" == "Y" ]; then
    echo ""
    echo -e "${YELLOW}Gmail SMTP settings: Host=smtp.gmail.com, Port=587${NC}"
    echo ""
    read -p "$(echo -e ${GREEN}SMTP Host ${NC}[smtp.gmail.com]: )" SMTP_HOST
    SMTP_HOST=${SMTP_HOST:-smtp.gmail.com}
    read -p "$(echo -e ${GREEN}SMTP Port ${NC}[587]: )" SMTP_PORT
    SMTP_PORT=${SMTP_PORT:-587}
    read -p "$(echo -e ${GREEN}SMTP Username ${NC}[your email]: )" SMTP_USER
    read -sp "$(echo -e ${GREEN}SMTP Password ${NC}[app password]: )" SMTP_PASSWORD
    echo ""
    read -p "$(echo -e ${GREEN}From Email ${NC}[${SMTP_USER}]: )" FROM_EMAIL
    FROM_EMAIL=${FROM_EMAIL:-$SMTP_USER}
else
    SMTP_HOST=""
    SMTP_PORT="587"
    SMTP_USER=""
    SMTP_PASSWORD=""
    FROM_EMAIL=""
fi

echo ""

# ─────────────────────────────────────────────────
# SECTION 7: SENTRY (Optional — error tracking)
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} SECTION 7: SENTRY ERROR TRACKING (Optional)${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Sentry catches errors in production and alerts you.${NC}"
echo -e "${YELLOW}Free tier: 5000 errors/month. Create at https://sentry.io${NC}"
echo -e "${YELLOW}Skip for now if not deploying yet.${NC}"
echo ""
read -p "$(echo -e ${GREEN}Sentry DSN ${NC}[leave blank to skip]: )" SENTRY_DSN

echo ""

# ─────────────────────────────────────────────────
# GENERATE SECRET KEY
# ─────────────────────────────────────────────────
echo -e "${YELLOW}Generating secure secret key...${NC}"
SECRET_KEY=$(openssl rand -hex 32)
echo -e "${GREEN}Secret key generated ✓${NC}"

echo ""

# ─────────────────────────────────────────────────
# CREATE BACKEND .env FILE
# ─────────────────────────────────────────────────
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE} CREATING CONFIGURATION FILES...${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cat > backend/.env << EOF
# ═══════════════════════════════════════════════════
# BACKEND ENVIRONMENT VARIABLES
# Generated by setup.sh on $(date)
# ═══════════════════════════════════════════════════

# Application
APP_NAME=${FULL_NAME} Portfolio API
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=${DATABASE_URL}

# Redis
REDIS_URL=${REDIS_URL}

# JWT Secrets (auto-generated — NEVER share this!)
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=${CORS_ORIGINS}

# OAuth - GitHub
GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
GITHUB_REDIRECT_URI=${GITHUB_REDIRECT_URI}

# OAuth - Google
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI}

# Email (SMTP)
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT}
SMTP_USER=${SMTP_USER}
SMTP_PASSWORD=${SMTP_PASSWORD}
FROM_EMAIL=${FROM_EMAIL}
ADMIN_EMAIL=${ADMIN_EMAIL}

# GitHub API (for portfolio stats)
GITHUB_USERNAME=${GITHUB_USERNAME}
GITHUB_TOKEN=${GITHUB_TOKEN}

# Sentry (Error Tracking)
SENTRY_DSN=${SENTRY_DSN}

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5
CONTACT_RATE_LIMIT_PER_HOUR=3
EOF

echo -e "${GREEN}✓ Created: backend/.env${NC}"

# ─────────────────────────────────────────────────
# CREATE FRONTEND .env.local FILE
# ─────────────────────────────────────────────────
cat > frontend/.env.local << EOF
# ═══════════════════════════════════════════════════
# FRONTEND ENVIRONMENT VARIABLES
# Generated by setup.sh on $(date)
# ═══════════════════════════════════════════════════

NEXT_PUBLIC_API_URL=${BACKEND_URL}
NEXT_PUBLIC_APP_NAME=${FULL_NAME} Portfolio
NEXT_PUBLIC_GITHUB_USERNAME=${GITHUB_USERNAME}
EOF

echo -e "${GREEN}✓ Created: frontend/.env.local${NC}"

echo ""

# ─────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    ✅ SETUP COMPLETE!                        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Files created:${NC}"
echo -e "  ${GREEN}✓${NC} backend/.env"
echo -e "  ${GREEN}✓${NC} frontend/.env.local"
echo ""
echo -e "${BOLD}Your configuration:${NC}"
echo -e "  Name:          ${FULL_NAME}"
echo -e "  Email:         ${ADMIN_EMAIL}"
echo -e "  GitHub:        ${GITHUB_USERNAME}"
echo -e "  Frontend URL:  ${FRONTEND_URL}"
echo -e "  Backend URL:   ${BACKEND_URL}"
echo -e "  Database:      $([ "$DB_CHOICE" == "2" ] && echo "Supabase (cloud)" || echo "Local Docker")"
echo -e "  Redis:         $([ "$REDIS_CHOICE" == "2" ] && echo "Upstash (cloud)" || echo "Local Docker")"
echo -e "  GitHub OAuth:  $([ -n "$GITHUB_CLIENT_ID" ] && echo "✓ Configured" || echo "✗ Skipped")"
echo -e "  Google OAuth:  $([ -n "$GOOGLE_CLIENT_ID" ] && echo "✓ Configured" || echo "✗ Skipped")"
echo -e "  Email:         $([ -n "$SMTP_HOST" ] && echo "✓ Configured" || echo "✗ Skipped")"
echo -e "  Sentry:        $([ -n "$SENTRY_DSN" ] && echo "✓ Configured" || echo "✗ Skipped")"
echo ""
echo -e "${BOLD}${YELLOW}NEXT STEPS:${NC}"
echo ""

if [ "$DB_CHOICE" == "1" ] || [ "$REDIS_CHOICE" == "1" ]; then
    echo -e "  ${BOLD}Option A: Run with Docker (easiest):${NC}"
    echo -e "    docker-compose up -d"
    echo ""
    echo -e "  ${BOLD}Option B: Run without Docker:${NC}"
fi

echo -e "  ${BOLD}Backend:${NC}"
echo -e "    cd backend"
echo -e "    python -m venv venv"
echo -e "    source venv/bin/activate    # On Windows: venv\\Scripts\\activate"
echo -e "    pip install -r requirements.txt"
echo -e "    alembic upgrade head        # Run database migrations"
echo -e "    uvicorn app.main:app --reload"
echo ""
echo -e "  ${BOLD}Frontend (new terminal):${NC}"
echo -e "    cd frontend"
echo -e "    npm install"
echo -e "    npm run dev"
echo ""
echo -e "  ${BOLD}Open in browser:${NC}"
echo -e "    Frontend: http://localhost:3000"
echo -e "    Backend API: http://localhost:8000"
echo -e "    API Docs: http://localhost:8000/docs"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"
echo ""
