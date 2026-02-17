# How to Create an Alert for Engineering Manager Positions at Meta

This guide shows you how to create a job alert for Engineering Manager positions at Meta.

## Prerequisites

1. **API Server Running**
   ```bash
   python3 -m uvicorn src.api.app:app --reload --port 8000
   ```

2. **User Account**
   - You need to be registered and logged in
   - You'll need your JWT access token

## Step-by-Step Guide

### Step 1: Register (if you don't have an account)

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "your_secure_password",
    "full_name": "Your Name"
  }'
```

**Response:**
```json
{
  "id": "user-uuid-here",
  "email": "your@email.com",
  "full_name": "Your Name",
  "is_active": true,
  "created_at": "2025-12-06T12:00:00Z"
}
```

### Step 2: Login to Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=your_secure_password"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the `access_token` - you'll need it for the next steps!**

### Step 3: Get Meta's Company ID

```bash
curl -X GET http://localhost:8000/api/v1/companies \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Look for Meta in the response and copy its `id` field.

**Alternative:** Query the database directly:
```sql
SELECT id, name FROM companies WHERE name = 'Meta';
```

### Step 4: Create the Alert

Replace:
- `YOUR_ACCESS_TOKEN` with your actual access token from Step 2
- `META_COMPANY_ID` with Meta's company UUID from Step 3

```bash
curl -X POST http://localhost:8000/api/v1/alerts/users/me/alerts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering Manager - Meta",
    "is_active": true,
    "company_ids": ["META_COMPANY_ID"],
    "keywords": ["engineering manager", "manager, engineering", "eng manager"],
    "excluded_keywords": [],
    "locations": [],
    "departments": [],
    "employment_types": [],
    "remote_types": [],
    "seniority_levels": [],
    "notification_method": "email",
    "notification_config": {"frequency": "immediate"}
  }'
```

**Response:**
```json
{
  "id": "alert-uuid-here",
  "user_id": "your-user-uuid",
  "name": "Engineering Manager - Meta",
  "is_active": true,
  "company_ids": ["meta-company-uuid"],
  "keywords": ["engineering manager", "manager, engineering", "eng manager"],
  "notification_method": "email",
  "notification_config": {"frequency": "immediate"},
  "created_at": "2025-12-06T12:00:00Z",
  "trigger_count": 0
}
```

### Step 5: Test the Alert

Test your alert to see how many jobs currently match:

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/alerts/ALERT_ID/test?limit=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "matching_jobs_count": 12,
  "total_active_jobs": 150,
  "sample_jobs": [
    {
      "id": "job-uuid",
      "title": "Engineering Manager, Infrastructure",
      "company": {
        "id": "meta-uuid",
        "name": "Meta"
      },
      "location": "Menlo Park, CA",
      "match_score": 1.0
    }
  ]
}
```

## Alert Configuration Explained

- **`name`**: Human-readable name for your alert
- **`is_active`**: Whether the alert is active (true/false)
- **`company_ids`**: Array of company UUIDs to monitor (just Meta in this case)
- **`keywords`**: Job titles must contain at least one of these keywords
  - "engineering manager" - matches "Engineering Manager"
  - "manager, engineering" - matches "Manager, Engineering"
  - "eng manager" - matches "Eng Manager"
- **`excluded_keywords`**: Jobs containing these keywords will be excluded
- **`locations`**: Filter by location (empty = all locations)
- **`departments`**: Filter by department (empty = all departments)
- **`notification_method`**: How to notify (email/webhook/push)
- **`notification_config`**: Notification settings
  - `frequency`: "immediate" or "daily"

## Managing Your Alerts

### List All Your Alerts
```bash
curl -X GET http://localhost:8000/api/v1/alerts/users/me/alerts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update an Alert
```bash
curl -X PATCH http://localhost:8000/api/v1/alerts/alerts/ALERT_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### Delete an Alert
```bash
curl -X DELETE http://localhost:8000/api/v1/alerts/alerts/ALERT_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Using the Web UI

You can also use the interactive API documentation:
1. Open http://localhost:8000/docs
2. Click "Authorize" and enter your access token
3. Navigate to the Alerts section
4. Use the "Try it out" feature to create/manage alerts

## Troubleshooting

**Error: "Meta company not found"**
- Run: `python scripts/migrate_companies_to_db.py`

**Error: "Unauthorized"**
- Your access token may have expired
- Login again to get a new token

**Error: "You can only create alerts for yourself"**
- Make sure you're using the `/users/me/alerts` endpoint
- Or use `/users/{user_id}/alerts` with your own user ID

