# API Usage Guide

## Overview

The Career Scraper API provides endpoints to scrape job listings from various companies, starting with Apple.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required (development mode).

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Scrape Apple Jobs (GET)

**GET** `/api/v1/scraper/scrape/apple`

Scrape job listings from Apple.

**Query Parameters:**
- `location` (optional): Location filter. Default: `israel-ISR`
  - Options: `israel-ISR`, `united-states-USA`, etc.
- `background` (optional): Run in background. Default: `false`

**Response:**
```json
{
  "status": "success",
  "company": "Apple",
  "location": "israel-ISR",
  "total_jobs": 20,
  "scraped_at": "2025-11-22T23:00:00.000000",
  "jobs": [
    {
      "title": "Design Engineer for SOC Group",
      "location": "Israel",
      "url": "https://jobs.apple.com/en-il/details/200633299",
      "description": "In this role you will be familiar with...",
      "team": "Hardware",
      "job_id": "200633299"
    },
    {
      "title": "Chip Level Integration Engineer",
      "location": "Herzliya",
      "url": "https://jobs.apple.com/en-il/details/200632762",
      "description": "...",
      "team": "Hardware",
      "job_id": "200632762"
    }
  ]
}
```

**Examples:**

```bash
# Scrape Apple jobs from Israel
curl http://localhost:8000/api/v1/scraper/scrape/apple

# Scrape Apple jobs from Israel (explicit)
curl http://localhost:8000/api/v1/scraper/scrape/apple?location=israel-ISR

# Scrape in background
curl http://localhost:8000/api/v1/scraper/scrape/apple?background=true
```

**JavaScript/Fetch:**
```javascript
// Simple GET request
fetch('http://localhost:8000/api/v1/scraper/scrape/apple')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.total_jobs} jobs`);
    data.jobs.forEach(job => {
      console.log(`${job.title} - ${job.location}`);
    });
  });

// With location parameter
fetch('http://localhost:8000/api/v1/scraper/scrape/apple?location=israel-ISR')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Python/Requests:**
```python
import requests

# Simple request
response = requests.get('http://localhost:8000/api/v1/scraper/scrape/apple')
data = response.json()

print(f"Found {data['total_jobs']} jobs")
for job in data['jobs']:
    print(f"{job['title']} - {job['location']}")
    print(f"  URL: {job['url']}")
```

---

### 3. Scrape Apple Jobs (POST)

**POST** `/api/v1/scraper/scrape/apple`

Scrape Apple jobs with custom location filters.

**Request Body:**
```json
{
  "location": "israel-ISR",
  "location_keywords": ["Israel", "Herzliya", "Tel Aviv", "Haifa"]
}
```

**Response:** Same as GET endpoint

**Examples:**

```bash
# cURL
curl -X POST http://localhost:8000/api/v1/scraper/scrape/apple \
  -H "Content-Type: application/json" \
  -d '{
    "location": "israel-ISR",
    "location_keywords": ["Israel", "Herzliya", "Tel Aviv"]
  }'
```

**JavaScript/Fetch:**
```javascript
fetch('http://localhost:8000/api/v1/scraper/scrape/apple', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    location: 'israel-ISR',
    location_keywords: ['Israel', 'Herzliya', 'Tel Aviv', 'Haifa']
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

**Python/Requests:**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/scraper/scrape/apple',
    json={
        'location': 'israel-ISR',
        'location_keywords': ['Israel', 'Herzliya', 'Tel Aviv', 'Haifa']
    }
)

data = response.json()
print(f"Found {data['total_jobs']} jobs")
```

---

### 4. List Available Companies

**GET** `/api/v1/scraper/scrape/companies`

Get list of all companies that can be scraped.

**Response:**
```json
{
  "companies": [
    {
      "name": "Apple",
      "endpoint": "/api/v1/scraper/scrape/apple",
      "status": "active",
      "method": "embedded_json",
      "locations": ["israel-ISR", "united-states-USA"]
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/scraper/scrape/companies
```

---

## Running the API

### Start the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Access Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Scraping failed

**Error Response:**
```json
{
  "detail": "Error message here"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Use responsibly.

---

## Complete Example: React Component

```jsx
import React, { useState, useEffect } from 'react';

function AppleJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/scraper/scrape/apple')
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch');
        return response.json();
      })
      .then(data => {
        setJobs(data.jobs);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading Apple jobs...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Apple Jobs ({jobs.length})</h1>
      <ul>
        {jobs.map(job => (
          <li key={job.job_id}>
            <h3>{job.title}</h3>
            <p>{job.location}</p>
            <p>{job.description}</p>
            <a href={job.url} target="_blank" rel="noopener noreferrer">
              Apply
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AppleJobs;
```

---

## Next Steps

- Add more company scrapers
- Implement authentication
- Add rate limiting
- Add caching
- Add webhooks for background jobs

