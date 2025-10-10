# Fix Railway Deployment Error

## The Problem

Your Railway deployment failed with this error:
```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
anthropic_api_key
  Field required [type=missing, input_value={}, input_type=dict]
database_url
  Field required [type=missing, input_value={}, input_type=dict]
```

## Why This Happened

Railway tried to **build your application before environment variables were set**. The application requires `ANTHROPIC_API_KEY` and `DATABASE_URL` to start, but they weren't available during the build.

## The Fix - 3 Steps

### Step 1: Set Environment Variables in Railway

**GOOD NEWS**: I've updated the code to automatically convert Railway's `DATABASE_URL` format! You can now use Railway's DATABASE_URL directly without modification.

1. Go to your Railway project dashboard
2. Click on your API service (the one that failed)
3. Go to the "Variables" tab
4. Add these variables **now** (before redeploying):

```bash
# REQUIRED - Add these first
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-api-key-here
ENVIRONMENT=production
DEBUG=False

# REQUIRED - Your frontend domain (update this!)
ALLOWED_ORIGINS=https://your-frontend-domain.com

# REQUIRED - Database URL
# ✅ SIMPLE METHOD: Just copy Railway's DATABASE_URL as-is!
# The code now automatically converts postgresql:// to postgresql+asyncpg://
#
# Go to your PostgreSQL service → Variables tab → Copy the DATABASE_URL value
# Paste it here exactly as Railway provides it
DATABASE_URL=${{Postgres.DATABASE_URL}}

# OR if you want to be explicit, you can still use the full URL:
# DATABASE_URL=postgresql://postgres:password@host.railway.internal:5432/railway
# (The code will automatically convert it to use asyncpg)

# REQUIRED - Redis URL (Railway provides this automatically)
REDIS_URL=${{Redis.REDIS_URL}}

# Optional - Adjust if needed
DAILY_COST_LIMIT_USD=5.0
DAILY_REQUEST_LIMIT=1000
RATE_LIMIT_PER_MINUTE=10
```

### Step 2: Redeploy

After setting the environment variables:

1. Go to the "Deployments" tab in Railway
2. Click "Redeploy" on the latest deployment

   OR

   Push a new commit to trigger a deployment:
   ```bash
   git add .
   git commit -m "Fix Railway configuration"
   git push origin main
   ```

### Step 3: Run Migrations

After successful deployment:

**Option A: Via Railway CLI** (recommended)
```bash
# Install Railway CLI if you haven't
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run alembic upgrade head
```

**Option B: Via Procfile** (automatic)
If migrations don't run automatically, update your `Procfile`:
```
release: alembic upgrade head
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Then redeploy.

## Verify Deployment

After deployment succeeds, test these endpoints:

1. **Basic health check**:
   ```bash
   curl https://your-app.railway.app/health
   ```

   Should return:
   ```json
   {
     "status": "healthy",
     "environment": "production"
   }
   ```

2. **Detailed health check**:
   ```bash
   curl https://your-app.railway.app/health/detailed
   ```

   Should show all services as "healthy".

3. **Test chat endpoint**:
   ```bash
   curl -X POST https://your-app.railway.app/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello!"}'
   ```

   Should return an AI response.

## Important Notes

### About DATABASE_URL - NOW AUTOMATIC! ✅

**Good news!** I've updated the code to automatically handle Railway's DATABASE_URL format.

Railway provides:
```
postgresql://postgres:password@host.railway.internal:5432/railway
```

Our app needs:
```
postgresql+asyncpg://postgres:password@host.railway.internal:5432/railway
```

**The app now automatically converts it!** Just use Railway's DATABASE_URL as-is:

```bash
# In your API service's Variables, just reference Railway's PostgreSQL DATABASE_URL:
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

The code will automatically add `+asyncpg` when connecting to the database.

**How it works:**
- I added an `async_database_url` property in `app/config.py`
- It checks if the URL starts with `postgresql://`
- If yes, it automatically converts to `postgresql+asyncpg://`
- If already has `+asyncpg`, it leaves it unchanged

This means you can use Railway's variable references directly without manual editing!

### About REDIS_URL

Railway's Redis service automatically sets `REDIS_URL` with the correct format. Just reference it:
```
REDIS_URL=${{Redis.REDIS_URL}}
```

### About ALLOWED_ORIGINS

This is your frontend domain(s). Update it to your actual domain:
```bash
# Single domain
ALLOWED_ORIGINS=https://yourdomain.com

# Multiple domains (comma-separated)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Troubleshooting

### Still getting "Field required" error?

Make sure:
- [ ] All variables from Step 1 are set in Railway
- [ ] Variables are set in the **API service** (not the database services)
- [ ] You've redeployed after setting variables

### Database connection error?

Check:
- [ ] `DATABASE_URL` has `+asyncpg` in it
- [ ] PostgreSQL service is running
- [ ] You're using Railway's internal database URL (not external)

### Redis connection error?

Check:
- [ ] Redis service is running
- [ ] `REDIS_URL` is set correctly
- [ ] You're using Railway's internal Redis URL

### CORS errors?

Update `ALLOWED_ORIGINS` to match your frontend domain exactly:
```bash
ALLOWED_ORIGINS=https://your-actual-frontend-domain.com
```

### Migrations not running?

Run manually:
```bash
railway run alembic upgrade head
```

## Next Steps After Successful Deployment

1. ✅ Test all endpoints
2. ✅ Monitor logs: `railway logs --follow`
3. ✅ Check `/metrics` endpoint for usage
4. ✅ Update frontend to use Railway API URL
5. ✅ Set up custom domain (optional)
6. ✅ Monitor costs at `/api/budget/status`

## Need More Help?

- **Quick Start Guide**: `docs/RAILWAY_QUICK_START.md`
- **Full Deployment Guide**: `docs/DEPLOYMENT.md`
- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway

---

Good luck! Your deployment should work now. 🚀
