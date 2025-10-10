# Railway Deployment - Quick Start Guide

This guide helps you deploy the Portfolio Chatbot API to Railway **in the correct order** to avoid build errors.

## Problem: Build Fails with "Field required" Error

If you see this error during Railway deployment:
```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
anthropic_api_key
  Field required [type=missing, input_value={}, input_type=dict]
database_url
  Field required [type=missing, input_value={}, input_type=dict]
```

This happens because **Railway tries to build before environment variables are set**. Follow the correct deployment order below.

---

## Correct Deployment Order

### Step 1: Create Railway Project (DO NOT Deploy Yet)

1. Go to [railway.app/new](https://railway.app/new)
2. Click "Deploy from GitHub repo"
3. **IMPORTANT**: Select "Empty Project" or "Create New Project" first (don't deploy yet!)
4. Name your project (e.g., "portfolio-chatbot")

### Step 2: Add Databases FIRST

**Add PostgreSQL:**
1. In your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will create the database and set these variables automatically:
   - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`
   - `DATABASE_URL` (but in wrong format for asyncpg)

**Add Redis:**
1. Click "+ New" again
2. Select "Database" → "Add Redis"
3. Railway will set `REDIS_URL` automatically

### Step 3: Connect GitHub Repository

1. Click "+ New" → "GitHub Repo"
2. Select your repository
3. **DO NOT click "Deploy" yet!**

### Step 4: Set Environment Variables BEFORE First Deploy

In your API service (the GitHub repo), go to "Variables" tab and add these **before deploying**:

```bash
# REQUIRED - Set these first!
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
ENVIRONMENT=production
DEBUG=False

# REQUIRED - Update with your frontend domain
ALLOWED_ORIGINS=https://your-frontend-domain.com

# PostgreSQL - Convert Railway's DATABASE_URL to asyncpg format
# Railway provides: postgresql://user:pass@host:port/db
# We need: postgresql+asyncpg://user:pass@host:port/db
DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}

# Redis - Use Railway's REDIS_URL (already correct format)
REDIS_URL=${{Redis.REDIS_URL}}

# Optional - Adjust if needed
DAILY_COST_LIMIT_USD=5.0
DAILY_REQUEST_LIMIT=1000
RATE_LIMIT_PER_MINUTE=10
```

**IMPORTANT DATABASE_URL FORMAT:**
Railway provides `DATABASE_URL` in this format:
```
postgresql://user:password@host:port/database
```

But we need the `asyncpg` driver:
```
postgresql+asyncpg://user:password@host:port/database
```

Use the template variable syntax shown above, or manually add `+asyncpg` after `postgresql`.

### Step 5: Deploy

Now you can deploy:
1. Go to "Deployments" tab
2. Click "Deploy" or wait for automatic deployment
3. Railway will:
   - Build your application
   - Run migrations (via Procfile)
   - Start the server

### Step 6: Run Migrations (if needed)

If migrations didn't run automatically:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run alembic upgrade head
```

### Step 7: Verify Deployment

**Check health endpoint:**
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

**Check detailed health:**
```bash
curl https://your-app.railway.app/health/detailed
```

Should show all services as "healthy".

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-api03-...` |
| `DATABASE_URL` | PostgreSQL URL with asyncpg | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://default:pass@...` |
| `ENVIRONMENT` | Environment name | `production` |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_ORIGINS` | CORS origins | `https://yourdomain.com` |

### Optional Variables (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `DAILY_COST_LIMIT_USD` | `5.0` | Daily cost budget |
| `DAILY_REQUEST_LIMIT` | `1000` | Daily request limit |
| `RATE_LIMIT_PER_MINUTE` | `10` | Requests per minute |
| `RATE_LIMIT_PER_HOUR` | `50` | Requests per hour |
| `LLM_MODEL` | `claude-3-5-haiku-20241022` | Claude model |
| `MAX_TOKENS` | `1000` | Max response tokens |
| `TEMPERATURE` | `0.7` | LLM temperature |
| `SESSION_TTL_HOURS` | `24` | Session lifetime |

---

## Troubleshooting

### Error: "Field required" during build

**Cause**: Environment variables not set before deployment.

**Fix**:
1. Cancel/pause deployment
2. Set all required environment variables (Step 4 above)
3. Redeploy

### Error: "Could not connect to database"

**Cause**: Wrong `DATABASE_URL` format (missing `+asyncpg`).

**Fix**: Update `DATABASE_URL` to include `+asyncpg`:
```bash
DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
```

### Error: "Redis connection refused"

**Cause**: Redis service not running or wrong URL.

**Fix**:
1. Check Redis service is running in Railway
2. Verify `REDIS_URL` variable is set correctly
3. Use Railway's internal Redis URL (not external)

### Migrations not running

**Cause**: Procfile not executing or migration error.

**Fix**:
```bash
railway run alembic upgrade head
```

Check logs for specific migration errors.

### CORS errors from frontend

**Cause**: Frontend domain not in `ALLOWED_ORIGINS`.

**Fix**: Update `ALLOWED_ORIGINS`:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Post-Deployment Checklist

- [ ] All environment variables set
- [ ] Database migrations completed
- [ ] `/health` endpoint returns 200
- [ ] `/health/detailed` shows all services healthy
- [ ] Can send chat message via `/api/chat`
- [ ] CORS works with frontend
- [ ] Logs show no errors
- [ ] Custom domain configured (optional)

---

## Useful Commands

```bash
# View logs
railway logs --follow

# Run migrations
railway run alembic upgrade head

# Open database shell
railway run psql $DATABASE_URL

# Check environment variables
railway variables

# Redeploy
railway up
```

---

## Getting Help

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Check Logs**: Railway Dashboard → Deployments → Logs
- **Database Access**: Railway Dashboard → PostgreSQL → Connect

---

## Success!

Once deployed, your API will be available at:
```
https://your-app-name.railway.app
```

Test it:
```bash
curl -X POST https://your-app-name.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

You should get a response from the AI chatbot! 🎉
