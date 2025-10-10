# Deployment Guide - Railway

This guide covers deploying the Portfolio Chatbot API to Railway.

> **🚨 IMPORTANT**: If you're getting "Field required" errors during deployment, see [RAILWAY_QUICK_START.md](./RAILWAY_QUICK_START.md) for the correct deployment order.

## Quick Links

- **Quick Start Guide**: [RAILWAY_QUICK_START.md](./RAILWAY_QUICK_START.md) - Follow this first!
- **Troubleshooting**: See section below for common issues

## Table of Contents
- [Prerequisites](#prerequisites)
- [Railway Setup](#railway-setup)
- [Database Configuration](#database-configuration)
- [Redis Configuration](#redis-configuration)
- [Environment Variables](#environment-variables)
- [Deployment Steps](#deployment-steps)
- [Running Migrations](#running-migrations)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Anthropic API Key**: Get one from [console.anthropic.com](https://console.anthropic.com)
3. **GitHub Repository**: Your code should be in a GitHub repository
4. **Railway CLI** (optional but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

---

## Railway Setup

### Option 1: Deploy via Railway Dashboard (Recommended)

1. **Create New Project**:
   - Go to [railway.app/new](https://railway.app/new)
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Choose the `chatbot-backend` directory if in a monorepo

2. **Add PostgreSQL Service**:
   - Click "+ New" in your project
   - Select "Database" → "PostgreSQL"
   - Railway will automatically provision a PostgreSQL database
   - Copy the `DATABASE_URL` from the PostgreSQL service

3. **Add Redis Service**:
   - Click "+ New" in your project
   - Select "Database" → "Redis"
   - Railway will automatically provision a Redis instance
   - Copy the `REDIS_URL` from the Redis service

### Option 2: Deploy via Railway CLI

```bash
# Initialize Railway project
railway init

# Link to existing project (if created via dashboard)
railway link

# Add PostgreSQL
railway add --database postgresql

# Add Redis
railway add --database redis
```

---

## Database Configuration

### PostgreSQL Setup

Railway automatically creates a PostgreSQL database with the following environment variables:
- `DATABASE_URL`: Connection string in format `postgresql://user:password@host:port/database`

**Important**: Our app uses `asyncpg`, so we need to modify the URL:

1. In Railway dashboard, go to your API service
2. Add a new environment variable:
   ```
   DATABASE_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
   ```

   This will automatically use Railway's PostgreSQL connection details.

### Running Database Migrations

After deployment, you need to run Alembic migrations:

```bash
# Using Railway CLI
railway run alembic upgrade head

# Or create a one-off deployment command
railway run --service your-api-service bash -c "alembic upgrade head"
```

**Alternative**: Add migration to startup:
- Modify `Procfile`:
  ```
  release: alembic upgrade head
  web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
  ```

---

## Redis Configuration

Railway automatically creates a Redis instance with:
- `REDIS_URL`: Connection string in format `redis://default:password@host:port`

No additional configuration needed - the app will use this URL directly.

---

## Environment Variables

### Setting Environment Variables in Railway

1. **Via Dashboard**:
   - Go to your API service
   - Click "Variables" tab
   - Add variables from `.env.production.example`

2. **Via CLI**:
   ```bash
   railway variables set ANTHROPIC_API_KEY=sk-ant-your-key-here
   railway variables set ENVIRONMENT=production
   railway variables set DEBUG=False
   ```

### Required Environment Variables

Copy these from `.env.production.example`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-production-key
ENVIRONMENT=production
DEBUG=False

# Update with your frontend domain
ALLOWED_ORIGINS=https://your-domain.com

# Database URLs (use Railway's internal URLs)
DATABASE_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
REDIS_URL=${REDIS_URL}

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=50
SESSION_MESSAGE_LIMIT=20
DAILY_REQUEST_LIMIT=1000

# Cost Controls
DAILY_COST_LIMIT_USD=5.0
COST_ALERT_THRESHOLD_USD=4.0

# LLM Configuration
LLM_MODEL=claude-3-5-haiku-20241022
MAX_TOKENS=1000
TEMPERATURE=0.7

# Session Configuration
SESSION_TTL_HOURS=24
CONVERSATION_HISTORY_LENGTH=10
```

### Railway-Managed Variables

Railway automatically sets:
- `PORT` - Application port (don't override this)
- `RAILWAY_ENVIRONMENT` - Current environment (production/staging)
- Database connection variables (`PGUSER`, `PGPASSWORD`, etc.)

---

## Deployment Steps

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Configure Railway Project

1. Create PostgreSQL and Redis services (see [Railway Setup](#railway-setup))
2. Add environment variables (see [Environment Variables](#environment-variables))
3. Railway will automatically detect `Procfile` and deploy

### Step 3: Run Database Migrations

```bash
railway run alembic upgrade head
```

### Step 4: Verify Deployment

Check your deployment:
```bash
# Get deployment URL
railway domain

# Test health endpoint
curl https://your-app.railway.app/health

# Test API
curl -X POST https://your-app.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

### Step 5: Monitor Logs

```bash
# View logs via CLI
railway logs

# Or view in Railway dashboard under "Deployments" tab
```

---

## Running Migrations

### Initial Migration (First Deployment)

```bash
railway run alembic upgrade head
```

### Future Migrations (After Schema Changes)

1. Create migration locally:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. Commit and push:
   ```bash
   git add alembic/versions/
   git commit -m "Add migration: Description"
   git push
   ```

3. Run migration on Railway:
   ```bash
   railway run alembic upgrade head
   ```

### Automatic Migrations (Optional)

Add to `Procfile`:
```
release: alembic upgrade head
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

This runs migrations automatically before each deployment.

---

## Monitoring

### Health Check Endpoint

Railway monitors: `https://your-app.railway.app/health`

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### Budget Status Endpoint

Monitor API costs:
```bash
curl https://your-app.railway.app/api/budget/status
```

Response:
```json
{
  "today_cost_usd": 0.0524,
  "today_requests": 150,
  "daily_cost_limit_usd": 5.0,
  "daily_request_limit": 1000,
  "cost_remaining_usd": 4.9476,
  "requests_remaining": 850,
  "cost_utilization_percent": 1.05,
  "request_utilization_percent": 15.0,
  "budget_exceeded": false
}
```

### Application Logs

View logs:
```bash
# Via CLI
railway logs --follow

# Via Dashboard
# Go to "Deployments" → Select deployment → "Logs" tab
```

### Metrics

Railway provides:
- CPU usage
- Memory usage
- Network traffic
- Request count
- Response times

Access via Railway Dashboard → "Metrics" tab

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Error**: `connection refused` or `could not connect to server`

**Solution**:
- Verify PostgreSQL service is running in Railway
- Check `DATABASE_URL` format includes `+asyncpg`:
  ```
  postgresql+asyncpg://user:password@host:port/database
  ```
- Ensure database service is in the same Railway project

#### 2. Redis Connection Errors

**Error**: `Error connecting to Redis`

**Solution**:
- Verify Redis service is running
- Check `REDIS_URL` is correctly set
- Ensure Redis service is in the same Railway project
- Use Railway's internal Redis URL (not external)

#### 3. Migrations Not Running

**Error**: `relation "sessions" does not exist`

**Solution**:
```bash
# Run migrations manually
railway run alembic upgrade head

# Or add to Procfile
release: alembic upgrade head
```

#### 4. CORS Errors

**Error**: `blocked by CORS policy`

**Solution**:
- Update `ALLOWED_ORIGINS` environment variable:
  ```
  ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
  ```
- Ensure no trailing slashes in URLs
- Redeploy after updating

#### 5. 429 Rate Limit Errors

**Error**: `Rate limit exceeded`

**Solution**:
- This is expected behavior (10 requests/minute)
- Increase limits if needed:
  ```
  RATE_LIMIT_PER_MINUTE=20
  RATE_LIMIT_PER_HOUR=100
  ```

#### 6. Budget Exceeded Errors

**Error**: `Daily cost budget has been reached`

**Solution**:
- Check budget status: `/api/budget/status`
- Increase limit if needed:
  ```
  DAILY_COST_LIMIT_USD=10.0
  ```
- Wait until next day (resets at midnight UTC)
- Clear cost tracking table if needed:
  ```sql
  railway run psql $DATABASE_URL -c "DELETE FROM cost_tracking WHERE date < CURRENT_DATE;"
  ```

#### 7. Deployment Build Failures

**Error**: Build fails or times out

**Solution**:
- Check `requirements.txt` for conflicting versions
- Ensure Python 3.10+ is specified (Railway auto-detects)
- Check Railway build logs for specific errors
- Try clearing Railway cache and rebuilding

#### 8. Environment Variables Not Loading

**Error**: `KeyError: 'ANTHROPIC_API_KEY'`

**Solution**:
- Verify all required env vars are set in Railway
- Check for typos in variable names
- Restart deployment after adding variables
- Use Railway CLI to verify:
  ```bash
  railway variables
  ```

### Getting Help

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Application Logs**: Check detailed error messages in Railway logs
- **Database Access**: Use Railway's built-in database client or:
  ```bash
  railway run psql $DATABASE_URL
  ```

---

## Production Checklist

Before going live:

- [ ] PostgreSQL service provisioned
- [ ] Redis service provisioned
- [ ] All environment variables set
- [ ] `ALLOWED_ORIGINS` updated with production domain
- [ ] `ANTHROPIC_API_KEY` set with production key
- [ ] Database migrations run successfully
- [ ] Health check endpoint returns 200
- [ ] CORS configured correctly
- [ ] Rate limiting tested
- [ ] Budget limits appropriate for production
- [ ] Monitoring/logging configured
- [ ] Custom domain configured (optional)
- [ ] SSL/HTTPS enabled (automatic on Railway)

---

## Custom Domain (Optional)

To use a custom domain:

1. **Add Domain in Railway**:
   - Go to your service → "Settings" → "Domains"
   - Click "Add Domain"
   - Enter your domain (e.g., `api.yourdomain.com`)

2. **Update DNS**:
   - Add CNAME record pointing to Railway's domain
   - Railway provides the specific CNAME target

3. **Update Environment**:
   ```
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

4. **Wait for DNS propagation** (up to 48 hours)

5. **SSL is automatic** - Railway handles HTTPS certificates

---

## Scaling

Railway automatically scales based on traffic. For manual control:

1. **Horizontal Scaling**: Not needed for most use cases (Railway handles this)
2. **Vertical Scaling**: Upgrade Railway plan for more resources
3. **Database Scaling**: Upgrade PostgreSQL/Redis plans as needed

---

## Backup and Recovery

### Database Backups

Railway provides automatic daily backups for paid plans.

**Manual Backup**:
```bash
# Export database
railway run pg_dump $DATABASE_URL > backup.sql

# Restore database
railway run psql $DATABASE_URL < backup.sql
```

### Environment Variables Backup

```bash
# Export variables
railway variables > env-backup.txt
```

---

## Security Best Practices

1. **API Keys**: Never commit API keys to version control
2. **Environment**: Always set `ENVIRONMENT=production` and `DEBUG=False`
3. **CORS**: Restrict `ALLOWED_ORIGINS` to your frontend domains only
4. **HTTPS**: Always use HTTPS in production (automatic on Railway)
5. **Rate Limiting**: Keep rate limits enabled
6. **Cost Controls**: Monitor `/api/budget/status` regularly
7. **Database**: Use Railway's internal URLs for better security
8. **Secrets**: Use Railway's secret variables for sensitive data

---

## Cost Optimization

1. **Enable Prompt Caching**: Already enabled in LLM service (90% cost reduction for cached tokens)
2. **Monitor Daily Budget**: Check `/api/budget/status` endpoint
3. **Adjust Limits**: Set appropriate `DAILY_COST_LIMIT_USD`
4. **Use Haiku Model**: `claude-3-5-haiku-20241022` is most cost-effective
5. **Optimize Context**: Only load necessary portfolio context
6. **Session Management**: 24-hour TTL prevents memory bloat
7. **Railway Costs**:
   - Free tier: $5/month credit
   - Hobby tier: $5/month + usage
   - Monitor Railway usage in dashboard

---

## Next Steps

After successful deployment:

1. Test all endpoints thoroughly
2. Monitor logs for first 24 hours
3. Set up alerting for budget thresholds
4. Configure custom domain (optional)
5. Share API URL with frontend team
6. Document any custom configurations

---

**Deployment Date**: _Add date here after deployment_
**Deployed By**: _Add your name_
**Railway Project**: _Add Railway project URL_
**Production URL**: _Add deployed URL_
