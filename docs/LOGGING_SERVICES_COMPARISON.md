# SaaS Logging Services Comparison

## Overview

For production server deployment, you need centralized logging to monitor workers, scrapers, and errors across multiple processes. Here are the best free/cheap options:

---

## Recommended Options

### 🏆 1. Better Stack (Logtail) - **RECOMMENDED**

**Pricing:**
- **Free Tier**: 1 GB/month, 3-day retention
- **Paid**: $0.25/GB after free tier (very affordable)
- **Retention**: Up to 1 year on paid plans

**Pros:**
- ✅ Best free tier (1 GB is generous)
- ✅ Beautiful, modern UI
- ✅ Fast search and filtering
- ✅ Real-time log streaming
- ✅ Built-in alerting (Slack, email, webhooks)
- ✅ Python SDK available
- ✅ Structured logging support (JSON)
- ✅ Easy integration with Loguru

**Cons:**
- ❌ Relatively new service (less mature than competitors)

**Best For:** Your use case - perfect balance of features and cost

**Integration:**
```python
pip install logtail-python
```

**Website:** https://betterstack.com/logs

---

### 2. Papertrail (by SolarWinds)

**Pricing:**
- **Free Tier**: 50 MB/month, 48-hour retention, 1 system
- **Paid**: $7/month for 1 GB, 1-year retention

**Pros:**
- ✅ Very reliable and mature
- ✅ Simple setup
- ✅ Good search capabilities
- ✅ Syslog compatible
- ✅ Alerts via email, Slack, webhooks

**Cons:**
- ❌ Small free tier (50 MB)
- ❌ Short retention on free tier (48 hours)
- ❌ Limited to 1 system on free tier

**Best For:** Small projects with low log volume

**Integration:**
```python
# Use syslog handler
```

**Website:** https://www.papertrail.com/

---

### 3. Logz.io

**Pricing:**
- **Free Tier**: 1 GB/day, 3-day retention
- **Paid**: $89/month for 5 GB/day

**Pros:**
- ✅ Generous free tier (1 GB/day!)
- ✅ Based on ELK stack (Elasticsearch, Logstash, Kibana)
- ✅ Powerful search and analytics
- ✅ Built-in dashboards
- ✅ AI-powered insights

**Cons:**
- ❌ Complex UI (can be overwhelming)
- ❌ Expensive paid tier
- ❌ Overkill for simple logging needs

**Best For:** Large-scale applications needing analytics

**Integration:**
```python
pip install logzio-python-handler
```

**Website:** https://logz.io/

---

### 4. Grafana Loki (Self-hosted or Cloud)

**Pricing:**
- **Self-hosted**: Free (you pay for server)
- **Grafana Cloud**: Free tier 50 GB logs/month, 14-day retention

**Pros:**
- ✅ Huge free tier on Grafana Cloud
- ✅ Integrates with Grafana dashboards
- ✅ Designed for high-volume logs
- ✅ Label-based indexing (efficient)

**Cons:**
- ❌ More complex setup
- ❌ Requires learning Grafana ecosystem
- ❌ LogQL query language learning curve

**Best For:** If you're already using Grafana for monitoring

**Integration:**
```python
pip install python-logging-loki
```

**Website:** https://grafana.com/products/cloud/logs/

---

### 5. Sentry (Error Tracking + Logs)

**Pricing:**
- **Free Tier**: 5,000 errors/month, 1 user
- **Paid**: $26/month for 50,000 errors

**Pros:**
- ✅ Excellent error tracking
- ✅ Stack traces and context
- ✅ Performance monitoring
- ✅ Release tracking
- ✅ Great Python integration

**Cons:**
- ❌ Focused on errors, not general logs
- ❌ Limited free tier
- ❌ Not ideal for info/debug logs

**Best For:** Error tracking (complement to logging service)

**Integration:**
```python
pip install sentry-sdk
```

**Website:** https://sentry.io/

---

## Comparison Table

| Service | Free Tier | Retention | Search | Alerts | Ease of Use | Best For |
|---------|-----------|-----------|--------|--------|-------------|----------|
| **Better Stack** | 1 GB/month | 3 days | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | **Recommended** |
| Papertrail | 50 MB/month | 48 hours | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | Small projects |
| Logz.io | 1 GB/day | 3 days | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐ | Analytics |
| Grafana Loki | 50 GB/month | 14 days | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐ | Grafana users |
| Sentry | 5K errors/month | 90 days | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ | Error tracking |

---

## Estimated Log Volume for Your Project

### Daily Scraping (13 companies)
- **Daily scraping task**: ~500 KB/day
- **Worker logs**: ~200 KB/day
- **Error logs**: ~100 KB/day (if issues occur)
- **Total**: ~800 KB/day = **24 MB/month**

### With Future Features (Users + Notifications)
- **User activity**: ~500 KB/day
- **Notification logs**: ~1 MB/day
- **Job matching**: ~300 KB/day
- **Total**: ~2.6 MB/day = **78 MB/month**

**Conclusion:** Even with all features, you'll stay well within Better Stack's 1 GB free tier.

---

## Recommended Setup: Better Stack + Sentry

### Better Stack (Logtail)
- **Use for**: General application logs (info, debug, warnings)
- **Cost**: Free (1 GB/month)
- **Setup**: 5 minutes

### Sentry
- **Use for**: Error tracking and performance monitoring
- **Cost**: Free (5,000 errors/month)
- **Setup**: 10 minutes

### Why Both?
- Better Stack: See what's happening (scraping progress, job counts, etc.)
- Sentry: Know when things break (errors, exceptions, performance issues)
- Combined cost: **$0/month** for your current scale

---

## Implementation Plan

### Phase 1: Better Stack Integration (30 minutes)

1. **Sign up for Better Stack**
   - Create account at https://betterstack.com/logs
   - Get source token

2. **Install Python SDK**
   ```bash
   pip install logtail-python
   ```

3. **Update `src/utils/logger.py`**
   ```python
   from logtail import LogtailHandler
   
   # Add Logtail handler
   if settings.logtail_source_token:
       logtail_handler = LogtailHandler(source_token=settings.logtail_source_token)
       logger.add(logtail_handler, level="INFO")
   ```

4. **Add to `.env`**
   ```bash
   LOGTAIL_SOURCE_TOKEN=your_token_here
   ```

5. **Add structured logging context**
   ```python
   logger.bind(
       company=company_name,
       task_id=task_id,
       session_id=session_id
   ).info("Scraping started")
   ```

### Phase 2: Sentry Integration (20 minutes)

1. **Sign up for Sentry**
   - Create account at https://sentry.io
   - Create new Python project
   - Get DSN

2. **Install SDK**
   ```bash
   pip install sentry-sdk
   ```

3. **Initialize in `src/workers/celery_app.py`**
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.celery import CeleryIntegration
   
   sentry_sdk.init(
       dsn=settings.sentry_dsn,
       integrations=[CeleryIntegration()],
       traces_sample_rate=0.1,  # 10% of transactions
       environment=settings.environment,
   )
   ```

4. **Add to `.env`**
   ```bash
   SENTRY_DSN=your_dsn_here
   ```

### Phase 3: Set Up Alerts (10 minutes)

**Better Stack:**
- Alert on ERROR level logs
- Alert on scraping failures
- Daily summary of scraping stats

**Sentry:**
- Alert on new errors
- Alert on error rate spikes
- Weekly performance digest

---

## Example: Structured Logging

### Before (Current)
```python
logger.info(f"Scraping {company_name} completed - found {job_count} jobs")
```

### After (Structured)
```python
logger.bind(
    company=company_name,
    job_count=job_count,
    duration_seconds=duration,
    session_id=session_id,
    task_id=task.request.id
).info("Scraping completed")
```

### Benefits
- **Searchable**: Find all logs for a specific company
- **Filterable**: Show only slow scraping sessions
- **Aggregatable**: Count jobs by company
- **Traceable**: Follow a session across multiple log entries

---

## Cost Projection

### Current (13 companies, daily scraping)
- Better Stack: **$0/month** (24 MB < 1 GB free tier)
- Sentry: **$0/month** (< 5,000 errors)
- **Total: $0/month**

### Future (100 companies, 1,000 users, notifications)
- Better Stack: **$0-5/month** (200-300 MB, still mostly free)
- Sentry: **$0/month** (still < 5,000 errors)
- **Total: $0-5/month**

### At Scale (500 companies, 10,000 users)
- Better Stack: **$15-20/month** (~2 GB)
- Sentry: **$26/month** (50,000 errors tier)
- **Total: $41-46/month**

---

## Next Steps

1. ✅ Task added to task list
2. ⏳ Sign up for Better Stack (5 min)
3. ⏳ Integrate Logtail handler (15 min)
4. ⏳ Add structured logging context (10 min)
5. ⏳ Set up alerts (10 min)
6. ⏳ (Optional) Add Sentry for error tracking (20 min)

**Total time: ~1 hour for complete logging infrastructure**

---

## Summary

**Recommended:** Better Stack (Logtail)
- ✅ 1 GB/month free tier (plenty for your needs)
- ✅ Beautiful UI and fast search
- ✅ Easy Python integration
- ✅ Built-in alerting
- ✅ Structured logging support
- ✅ Will stay free even with 100 companies

**Optional Add-on:** Sentry
- ✅ Excellent error tracking
- ✅ Free tier covers your needs
- ✅ Complements Better Stack perfectly

**Total Cost:** $0/month for foreseeable future 🎉

