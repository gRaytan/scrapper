# Example Use Cases
## Job Scraping & Alert Platform

This document provides concrete examples of how the system will work from a user's perspective.

---

## Use Case 1: Data Engineer Looking for Jobs in Israel

### User Profile
- **Name**: Sarah
- **Email**: sarah@example.com
- **Target Role**: Data Engineer
- **Target Companies**: Google, Meta, Wiz, Monday.com
- **Location**: Israel (Tel Aviv, Haifa)

### Setup
```python
# Create user
user = User.create(
    email='sarah@example.com',
    full_name='Sarah Cohen'
)

# Create alert
alert = Alert.create(
    user_id=user.id,
    name='Data Engineer - Israel - Top Companies',
    is_active=True,
    company_ids=[1, 2, 15, 16],  # Google, Meta, Wiz, Monday.com
    keywords=['Data Engineer', 'Data Engineering', 'Big Data', 'ETL'],
    excluded_keywords=['Intern', 'Junior'],
    locations=['Israel', 'Tel Aviv', 'Haifa'],
    notification_method='email'
)
```

### Daily Workflow

**Day 1 - Monday**
1. System scrapes all companies at midnight
2. Finds 3 new Data Engineer positions:
   - Google: "Senior Data Engineer" - Tel Aviv
   - Wiz: "Data Engineer - Cloud Security" - Tel Aviv
   - Monday.com: "Data Engineering Team Lead" - Tel Aviv
3. Alert matcher finds all 3 match Sarah's alert
4. Sarah receives email:

```
Subject: 🎯 3 New Jobs Match Your Alert: Data Engineer - Israel

Hi Sarah,

We found 3 new positions matching your alert "Data Engineer - Israel - Top Companies":

1. Senior Data Engineer at Google
   Location: Tel Aviv, Israel
   Posted: Today
   Apply: https://careers.google.com/jobs/12345

2. Data Engineer - Cloud Security at Wiz
   Location: Tel Aviv, Israel
   Posted: Today
   Apply: https://www.wiz.io/careers/data-engineer

3. Data Engineering Team Lead at Monday.com
   Location: Tel Aviv, Israel
   Posted: Today
   Apply: https://monday.com/careers/team-lead

---
Manage your alerts: https://jobscraper.com/alerts
Unsubscribe: https://jobscraper.com/unsubscribe
```

**Day 2 - Tuesday**
1. Sarah applies to Google and Wiz positions
2. She marks them in the system:
```python
UserJobApplication.create(
    user_id=sarah.id,
    job_position_id=google_job.id,
    status='applied',
    applied_at=datetime.now(),
    notes='Applied via LinkedIn'
)
```

**Day 7 - Next Monday**
1. System scrapes again
2. Google position is still active → updates `last_seen_at`
3. Wiz position is gone → marks as `expired`
4. Sarah receives update:

```
Subject: 📊 Weekly Summary - Your Tracked Positions

Hi Sarah,

Here's an update on positions you're tracking:

STILL ACTIVE (1):
✅ Senior Data Engineer at Google (Applied 5 days ago)

EXPIRED (1):
❌ Data Engineer - Cloud Security at Wiz (Applied 5 days ago)
   This position was likely filled or cancelled.

---
Keep track of your applications: https://jobscraper.com/applications
```

---

## Use Case 2: Software Engineer Targeting FAANG

### User Profile
- **Name**: David
- **Email**: david@example.com
- **Target Role**: Software Engineer, Backend Engineer
- **Target Companies**: Google, Meta, Amazon, Apple, Microsoft
- **Location**: United States (any) or Remote

### Setup
```python
user = User.create(
    email='david@example.com',
    full_name='David Miller'
)

# Alert 1: Senior positions at FAANG
alert1 = Alert.create(
    user_id=user.id,
    name='Senior Backend - FAANG',
    company_ids=[1, 2, 3, 4, 5],  # FAANG companies
    keywords=['Senior Software Engineer', 'Senior Backend', 'Staff Engineer'],
    excluded_keywords=['Manager', 'Director', 'Intern'],
    locations=['United States', 'Remote'],
    is_remote=None  # Don't care about remote vs office
)

# Alert 2: Remote-only positions
alert2 = Alert.create(
    user_id=user.id,
    name='Remote Backend - Any Company',
    keywords=['Backend Engineer', 'Software Engineer'],
    excluded_keywords=['Junior', 'Intern', 'Frontend'],
    is_remote=True  # Only remote positions
)
```

### Scenario: Multiple Alerts Triggered

**Day 1**
System finds:
1. "Senior Backend Engineer" at Google - Mountain View, CA
2. "Staff Software Engineer" at Meta - Remote
3. "Backend Engineer" at Wiz - Remote

**Alert Matching**:
- Position 1 matches Alert 1 only (FAANG, Senior, US location)
- Position 2 matches Alert 1 AND Alert 2 (FAANG, Senior, Remote)
- Position 3 matches Alert 2 only (Remote, but not FAANG)

**Email Sent**:
```
Subject: 🎯 3 New Jobs Match Your Alerts

Hi David,

ALERT: "Senior Backend - FAANG" (2 matches)
1. Senior Backend Engineer at Google
   Location: Mountain View, CA
   Apply: https://careers.google.com/jobs/...

2. Staff Software Engineer at Meta
   Location: Remote
   Apply: https://www.metacareers.com/jobs/...

ALERT: "Remote Backend - Any Company" (2 matches)
1. Staff Software Engineer at Meta
   Location: Remote
   Apply: https://www.metacareers.com/jobs/...

2. Backend Engineer at Wiz
   Location: Remote
   Apply: https://www.wiz.io/careers/...
```

---

## Use Case 3: Career Advisor Monitoring Market Trends

### User Profile
- **Name**: Rachel (Career Advisor)
- **Email**: rachel@university.edu
- **Goal**: Monitor job market for students
- **Interest**: All tech positions in Israel

### Setup
```python
user = User.create(
    email='rachel@university.edu',
    full_name='Rachel Levy',
    preferences={
        'role': 'career_advisor',
        'daily_digest': True
    }
)

# Broad alert for market monitoring
alert = Alert.create(
    user_id=user.id,
    name='All Tech Jobs - Israel Market',
    keywords=[],  # No keyword filter - get everything
    locations=['Israel', 'Tel Aviv', 'Haifa', 'Jerusalem'],
    notification_method='email',
    notification_config={
        'digest_mode': True,  # Daily digest instead of immediate
        'include_stats': True
    }
)
```

### Daily Digest Email
```
Subject: 📊 Daily Job Market Digest - Israel Tech (45 new positions)

Hi Rachel,

Here's your daily summary of the Israel tech job market:

NEW POSITIONS TODAY: 45

BY COMPANY:
- Google: 8 positions
- Microsoft: 6 positions
- Wiz: 5 positions
- Monday.com: 4 positions
- Meta: 3 positions
- Others: 19 positions

BY ROLE:
- Software Engineer: 18 positions
- Data Engineer: 7 positions
- Product Manager: 6 positions
- DevOps Engineer: 5 positions
- Security Engineer: 4 positions
- Others: 5 positions

BY LOCATION:
- Tel Aviv: 32 positions
- Haifa: 8 positions
- Jerusalem: 3 positions
- Remote: 2 positions

EXPIRED POSITIONS: 12
(Positions removed from career pages in the last 24h)

TRENDING:
📈 "Machine Learning" mentions up 25% this week
📈 "Cloud Security" positions up 40% this month

---
View full report: https://jobscraper.com/reports/daily
```

---

## Use Case 4: Excluded Keywords Example

### User Profile
- **Name**: Mike
- **Email**: mike@example.com
- **Goal**: Senior positions only, no management

### Setup
```python
alert = Alert.create(
    user_id=mike.id,
    name='Senior IC Roles - No Management',
    keywords=['Senior', 'Staff', 'Principal'],
    excluded_keywords=[
        'Manager', 'Director', 'VP', 'Head of',
        'Junior', 'Intern', 'Entry Level'
    ],
    locations=['United States', 'Remote']
)
```

### Matching Examples

**MATCH** ✅
- "Senior Software Engineer" - Contains "Senior", no excluded keywords
- "Staff Backend Engineer" - Contains "Staff", no excluded keywords
- "Principal Engineer - Infrastructure" - Contains "Principal", no excluded keywords

**NO MATCH** ❌
- "Engineering Manager" - Contains excluded keyword "Manager"
- "Senior Director of Engineering" - Contains excluded keyword "Director"
- "Junior Software Engineer" - Contains excluded keyword "Junior"
- "Head of Backend Engineering" - Contains excluded keyword "Head of"

---

## Use Case 5: Department-Specific Alert

### User Profile
- **Name**: Lisa
- **Email**: lisa@example.com
- **Interest**: Security roles only

### Setup
```python
alert = Alert.create(
    user_id=lisa.id,
    name='Security Engineering Roles',
    keywords=['Security', 'Cybersecurity', 'InfoSec'],
    departments=['Security', 'Information Security', 'Cyber Security'],
    locations=['Israel', 'United States', 'Remote']
)
```

### Matching Logic
```python
# Position 1
position = {
    'title': 'Senior Software Engineer',
    'department': 'Security',
    'location': 'Tel Aviv'
}
# MATCH ✅ - Department is "Security"

# Position 2
position = {
    'title': 'Security Engineer',
    'department': 'Engineering',
    'location': 'Tel Aviv'
}
# MATCH ✅ - Title contains "Security"

# Position 3
position = {
    'title': 'Software Engineer',
    'department': 'Product',
    'location': 'Tel Aviv'
}
# NO MATCH ❌ - No security keywords, wrong department
```

---

## Use Case 6: Application Tracking

### Scenario: Tracking Application Progress

```python
# User applies to a position
application = UserJobApplication.create(
    user_id=user.id,
    job_position_id=position.id,
    status='applied',
    applied_at=datetime.now(),
    notes='Applied via company website, referral from John'
)

# Update after phone screen
application.update(
    status='interviewing',
    notes='Phone screen completed, technical interview scheduled for next week'
)

# Update after offer
application.update(
    status='offered',
    notes='Received offer: $150k base + equity'
)

# Final decision
application.update(
    status='accepted',
    notes='Accepted offer, start date: Jan 15'
)
```

### Application Status Flow
```
interested → applied → interviewing → offered → accepted/rejected
```

### User Dashboard View
```
MY APPLICATIONS (15 total)

ACTIVE (8):
- Senior Data Engineer at Google (Interviewing)
  Applied: 2 weeks ago
  Last update: Phone screen completed

- Staff Engineer at Meta (Applied)
  Applied: 1 week ago
  Last update: Application submitted

OFFERS (2):
- Principal Engineer at Wiz (Offered)
  Applied: 3 weeks ago
  Offer: $160k + equity

CLOSED (5):
- Backend Engineer at Amazon (Rejected)
- Data Engineer at Microsoft (Rejected)
- ...
```

---

## Use Case 7: Position Lifecycle Tracking

### Scenario: Monitoring Position Availability

```python
# Day 1: Position first appears
position = JobPosition.create(
    company_id=google.id,
    title='Senior Data Engineer',
    location='Tel Aviv',
    job_url='https://careers.google.com/jobs/12345',
    status='active',
    first_seen_at='2025-01-01 00:00:00',
    last_seen_at='2025-01-01 00:00:00'
)

# Day 2-7: Position still active
# Each day: position.last_seen_at = current_timestamp

# Day 8: Position removed from career page
position.update(
    status='expired',
    expired_at='2025-01-08 00:00:00'
)

# Users who applied get notified
notify_users_of_expired_position(position)
```

### Analytics Query
```sql
-- How long do positions stay active on average?
SELECT 
    company.name,
    AVG(EXTRACT(EPOCH FROM (expired_at - first_seen_at))/86400) as avg_days_active
FROM job_positions
JOIN companies ON job_positions.company_id = companies.id
WHERE status = 'expired'
GROUP BY company.name
ORDER BY avg_days_active DESC;

-- Results:
-- Google: 21 days average
-- Meta: 18 days average
-- Startups: 14 days average
```

---

## Database Query Examples

### Find all active positions for a company
```python
positions = session.query(JobPosition).filter(
    JobPosition.company_id == google.id,
    JobPosition.status == 'active'
).all()
```

### Find positions matching an alert
```python
from sqlalchemy import or_, and_

# Get alert
alert = session.query(Alert).get(alert_id)

# Build query
query = session.query(JobPosition).filter(
    JobPosition.status == 'active'
)

# Company filter
if alert.company_ids:
    query = query.filter(JobPosition.company_id.in_(alert.company_ids))

# Keyword filter (any keyword in title)
if alert.keywords:
    keyword_filters = [
        JobPosition.title.ilike(f'%{kw}%') 
        for kw in alert.keywords
    ]
    query = query.filter(or_(*keyword_filters))

# Excluded keywords (none in title)
if alert.excluded_keywords:
    for excluded in alert.excluded_keywords:
        query = query.filter(~JobPosition.title.ilike(f'%{excluded}%'))

# Location filter
if alert.locations:
    location_filters = [
        JobPosition.location.ilike(f'%{loc}%') 
        for loc in alert.locations
    ]
    query = query.filter(or_(*location_filters))

# Remote filter
if alert.is_remote is not None:
    query = query.filter(JobPosition.is_remote == alert.is_remote)

matching_positions = query.all()
```

### Get user's application history
```python
applications = session.query(UserJobApplication).join(
    JobPosition
).join(
    Company
).filter(
    UserJobApplication.user_id == user.id
).order_by(
    UserJobApplication.applied_at.desc()
).all()

for app in applications:
    print(f"{app.job_position.title} at {app.job_position.company.name}")
    print(f"Status: {app.status}")
    print(f"Applied: {app.applied_at}")
    print("---")
```

---

## Summary

These use cases demonstrate:
- ✅ Flexible alert configuration
- ✅ Multi-criteria matching
- ✅ Application tracking
- ✅ Position lifecycle management
- ✅ Market trend monitoring
- ✅ Personalized notifications
- ✅ Historical data analysis

The system is designed to serve both individual job seekers and career professionals with comprehensive job market intelligence.

