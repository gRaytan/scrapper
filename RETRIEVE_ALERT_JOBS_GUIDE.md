# How to Retrieve All Jobs Matching an Alert

This guide shows you how to retrieve ALL jobs that match your alert criteria (for Engineering Manager positions at Meta).

## 🎯 Two Methods Available

### Method 1: Using the API (Recommended)
### Method 2: Using the Python Script

---

## Method 1: Using the API

### Step 1: Get Your Alert ID

First, list all your alerts to find the alert ID:

```bash
curl -X GET http://localhost:8000/api/v1/alerts/users/me/alerts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "total": 1,
  "alerts": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Engineering Manager - Meta",
      "is_active": true,
      "company_ids": ["meta-company-uuid"],
      "keywords": ["engineering manager", "manager, engineering", "eng manager"],
      ...
    }
  ]
}
```

Copy the `id` field - this is your alert ID.

### Step 2: Get ALL Matching Jobs

Use the new `/alerts/{alert_id}/matches` endpoint to retrieve ALL matching jobs:

```bash
curl -X GET "http://localhost:8000/api/v1/alerts/alerts/YOUR_ALERT_ID/matches" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "matching_jobs_count": 12,
  "total_active_jobs": 150,
  "retrieved_at": "2025-12-06T12:00:00Z",
  "jobs": [
    {
      "id": "job-uuid-1",
      "title": "Engineering Manager, Infrastructure",
      "company": {
        "id": "meta-uuid",
        "name": "Meta"
      },
      "location": "Menlo Park, CA",
      "department": "Engineering",
      "description": "We are looking for an experienced Engineering Manager...",
      "posted_date": "2025-12-01T10:00:00Z",
      "job_url": "https://www.metacareers.com/jobs/123456",
      "external_id": "123456",
      "is_remote": false,
      "employment_type": "full-time",
      "match_score": 1.0,
      "matched_criteria": ["keywords"]
    },
    {
      "id": "job-uuid-2",
      "title": "Manager, Engineering - AI/ML",
      "company": {
        "id": "meta-uuid",
        "name": "Meta"
      },
      "location": "Seattle, WA",
      ...
    }
  ]
}
```

### Difference Between Endpoints

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `POST /alerts/{alert_id}/test?limit=10` | Test alert with sample | Limited sample (max 50 jobs) |
| `GET /alerts/{alert_id}/matches` | Get all matching jobs | ALL matching jobs (unlimited) |

---

## Method 2: Using the Python Script

### Run the Script

```bash
python scripts/get_alert_matching_jobs.py YOUR_ALERT_ID
```

**Example:**
```bash
python scripts/get_alert_matching_jobs.py 123e4567-e89b-12d3-a456-426614174000
```

### Export to JSON File

To save the results to a JSON file:

```bash
python scripts/get_alert_matching_jobs.py YOUR_ALERT_ID --export-json
```

This will create a file in `data/exports/` with all matching jobs.

**Output:**
```
================================================================================
Retrieving All Jobs Matching Alert
================================================================================
✅ Found Alert: Engineering Manager - Meta
   User ID: user-uuid
   Active: True
   Company IDs: ['meta-uuid']
   Keywords: ['engineering manager', 'manager, engineering', 'eng manager']

📊 Querying database for active jobs...
   Total active jobs in database: 150

🔍 Filtering jobs by alert criteria...

✅ Found 12 matching jobs!

================================================================================
Matching Jobs
================================================================================

1. Engineering Manager, Infrastructure
   Company: Meta
   Location: Menlo Park, CA
   Department: Engineering
   Posted: 2025-12-01 10:00:00
   URL: https://www.metacareers.com/jobs/123456
   External ID: 123456
   Remote: False

2. Manager, Engineering - AI/ML
   Company: Meta
   Location: Seattle, WA
   ...

✅ Exported to: data/exports/alert_matches_123e4567_20251206_120000.json
```

---

## Using the Interactive Swagger UI

1. Open http://localhost:8000/docs
2. Click "Authorize" and enter your access token
3. Navigate to **GET /api/v1/alerts/alerts/{alert_id}/matches**
4. Click "Try it out"
5. Enter your alert ID
6. Click "Execute"
7. View all matching jobs in the response

---

## Response Fields Explained

- **`matching_jobs_count`**: Total number of jobs matching your alert
- **`total_active_jobs`**: Total active jobs in the database (all companies)
- **`retrieved_at`**: Timestamp when the data was retrieved
- **`jobs`**: Array of all matching jobs with full details:
  - `id`: Job UUID
  - `title`: Job title
  - `company`: Company info (id, name)
  - `location`: Job location
  - `department`: Department/team
  - `description`: Full job description
  - `posted_date`: When the job was posted
  - `job_url`: Link to apply
  - `external_id`: External job ID
  - `is_remote`: Whether it's a remote position
  - `employment_type`: Full-time, part-time, etc.
  - `match_score`: How well it matches (currently 1.0 for all)
  - `matched_criteria`: Which criteria matched

---

## Example: Complete Workflow

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=your_password"

# Save the access_token from response

# 2. List your alerts
curl -X GET http://localhost:8000/api/v1/alerts/users/me/alerts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Copy the alert ID

# 3. Get all matching jobs
curl -X GET "http://localhost:8000/api/v1/alerts/alerts/ALERT_ID/matches" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq '.'

# Use jq to pretty-print the JSON response
```

---

## Troubleshooting

**Error: "Alert not found"**
- Check that you're using the correct alert ID
- Make sure the alert exists in your account

**Error: "You can only access your own alerts"**
- You're trying to access someone else's alert
- Make sure you're logged in with the correct account

**No matching jobs found**
- The alert criteria might be too restrictive
- Check if Meta has any active jobs in the database
- Try the test endpoint first to see sample results

---

## Next Steps

Once you have the matching jobs, you can:
1. Review the job details
2. Apply to the positions via the `job_url`
3. Update your alert criteria if needed
4. Set up notifications to get alerted when new matching jobs are posted

