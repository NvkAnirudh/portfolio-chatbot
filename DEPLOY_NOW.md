# Deploy to Railway - Simple Guide

## What I Fixed

Your deployment was failing because:
1. Railway wasn't setting environment variables before building
2. The `DATABASE_URL` format issue (now **automatically fixed** in the code!)

## Steps to Deploy Now

### 1. Set These Variables in Railway

In your **API service** (chatbot-backend), go to Variables tab and set:

```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

**Note**: Replace `your-frontend-domain.com` with your actual frontend URL.

### 2. Push the Latest Code

```bash
git add .
git commit -m "Fix Railway deployment with automatic DATABASE_URL conversion"
git push origin main
```

### 3. Railway Will Auto-Deploy

Railway will detect the push and redeploy automatically.

### 4. Run Migrations (After Successful Build)

```bash
railway run alembic upgrade head
```

### 5. Test Your Deployment

```bash
curl https://your-app.railway.app/health/detailed
```

Should show all services as "healthy".

## What Changed in the Code

I added automatic `DATABASE_URL` conversion in `app/config.py`:
- Railway provides: `postgresql://...`
- App needs: `postgresql+asyncpg://...`
- **Now automatic**: The code converts it automatically!

You don't need to manually edit the DATABASE_URL anymore. Just use `${{Postgres.DATABASE_URL}}` directly.

## If It Still Fails

### Check These:

1. ✅ All variables are set in the **API service** (not in PostgreSQL/Redis services)
2. ✅ `ANTHROPIC_API_KEY` is your actual Anthropic API key
3. ✅ PostgreSQL and Redis services are running in Railway
4. ✅ You've pushed the latest code

### View Logs:

```bash
railway logs --follow
```

Look for any errors about missing variables or connection issues.

## Success Check

Once deployed, these endpoints should work:

```bash
# Basic health
curl https://your-app.railway.app/health

# Detailed health
curl https://your-app.railway.app/health/detailed

# Chat test
curl -X POST https://your-app.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## Need More Help?

- **Detailed fix**: See `RAILWAY_FIX.md`
- **Quick start**: See `docs/RAILWAY_QUICK_START.md`
- **Full guide**: See `docs/DEPLOYMENT.md`

---

**You're almost there!** Just set those 6 environment variables and push the code. 🚀
