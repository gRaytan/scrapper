# SQLAlchemy Models Created ✅

## Phase 3: Directory Structure & Models - COMPLETED

### ✅ Step 1: Directory Structure Created

```
src/
├── models/              ✅ Created
│   ├── __init__.py      ✅ Updated
│   ├── base.py          ✅ Existing (reviewed)
│   ├── company.py       ✅ Existing (reviewed)
│   ├── job_position.py  ✅ Updated (added lifecycle fields)
│   ├── user.py          ✅ Created
│   ├── alert.py         ✅ Created
│   ├── user_job_application.py  ✅ Created
│   └── alert_notification.py    ✅ Created
├── repositories/        ✅ Created (empty)
├── services/            ✅ Created (empty)
└── database/            ✅ Created (empty)

migrations/
└── versions/            ✅ Created (empty)
```

---

## ✅ Step 2: SQLAlchemy Models Implemented

### Model Summary

| Model | Table Name | Primary Key | Description |
|-------|-----------|-------------|-------------|
| **User** | `users` | UUID | User accounts and preferences |
| **Company** | `companies` | UUID | Company information and scraping config |
| **JobPosition** | `job_positions` | UUID | Job listings with lifecycle tracking |
| **Alert** | `alerts` | UUID | User alert configurations |
| **UserJobApplication** | `user_job_applications` | UUID | User application tracking |
| **AlertNotification** | `alert_notifications` | UUID | Notification audit log |

---

### 1. Base Models (`base.py`)

**Classes:**
- `Base` - SQLAlchemy declarative base
- `TimestampMixin` - Adds `created_at` and `updated_at` fields
- `UUIDMixin` - Adds UUID primary key

**Features:**
- All timestamps use timezone-aware datetime
- Automatic timestamp updates via `server_default` and `onupdate`
- UUID v4 for all primary keys

---

### 2. User Model (`user.py`)

**Table:** `users`

**Fields:**
- `id` (UUID) - Primary key
- `email` (String) - Unique, indexed
- `full_name` (String) - Optional
- `is_active` (Boolean) - Default True, indexed
- `last_login_at` (DateTime) - Optional
- `preferences` (JSON) - User preferences
- `created_at` (DateTime) - Auto-generated
- `updated_at` (DateTime) - Auto-updated

**Relationships:**
- `alerts` → One-to-many with Alert
- `applications` → One-to-many with UserJobApplication
- `notifications` → One-to-many with AlertNotification

**Properties:**
- `notification_email` - Get notification email from preferences
- `notification_enabled` - Check if notifications enabled
- `digest_mode` - Check if user prefers daily digest

---

### 3. Company Model (`company.py`)

**Table:** `companies`

**Fields:**
- `id` (UUID) - Primary key
- `name` (String) - Unique, indexed
- `website` (String)
- `careers_url` (String)
- `industry` (String) - Optional
- `size` (String) - Optional
- `location` (String) - Optional
- `scraping_config` (JSON) - Scraper configuration
- `scraping_frequency` (String) - Cron expression
- `last_scraped_at` (DateTime) - Optional
- `is_active` (Boolean) - Default True
- `created_at` (DateTime) - Auto-generated
- `updated_at` (DateTime) - Auto-updated

**Relationships:**
- `job_positions` → One-to-many with JobPosition
- `scraping_sessions` → One-to-many with ScrapingSession

**Properties:**
- `scraper_type` - Get scraper type from config
- `pagination_type` - Get pagination type from config
- `requires_js` - Check if JavaScript required
- `selectors` - Get CSS selectors from config

---

### 4. JobPosition Model (`job_position.py`)

**Table:** `job_positions`

**Fields:**
- `id` (UUID) - Primary key
- `company_id` (UUID) - Foreign key to companies, indexed
- `title` (String) - Indexed
- `description` (Text) - Optional
- `location` (String) - Indexed, optional
- `remote_type` (String) - remote/hybrid/onsite
- `employment_type` (String) - full-time/part-time/contract
- `department` (String) - Indexed, optional
- `seniority_level` (String) - entry/mid/senior/lead/executive
- `salary_range` (JSON) - Optional
- `requirements` (Array[Text]) - Optional
- `benefits` (Array[Text]) - Optional
- `application_url` (String) - Optional
- `job_url` (String) - Required
- `posted_date` (DateTime) - Optional
- `scraped_at` (DateTime) - Required, indexed
- **`status` (String) - active/expired/filled, indexed** ✨ NEW
- **`first_seen_at` (DateTime) - Indexed** ✨ NEW
- **`last_seen_at` (DateTime)** ✨ NEW
- **`expired_at` (DateTime) - Optional** ✨ NEW
- `is_active` (Boolean) - Deprecated, use status
- `raw_html` (Text) - Optional
- `extra_metadata` (JSON) - Optional
- `created_at` (DateTime) - Auto-generated
- `updated_at` (DateTime) - Auto-updated

**Relationships:**
- `company` → Many-to-one with Company

**Indexes:**
- `ix_job_positions_company_active` - (company_id, is_active)
- `ix_job_positions_location_active` - (location, is_active)
- `ix_job_positions_department_active` - (department, is_active)

**Properties:**
- `salary_min` - Get minimum salary
- `salary_max` - Get maximum salary
- `salary_currency` - Get salary currency

---

### 5. Alert Model (`alert.py`)

**Table:** `alerts`

**Fields:**
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users, indexed
- `name` (String) - Alert name
- `is_active` (Boolean) - Default True, indexed
- `company_ids` (Array[UUID]) - Company filter
- `keywords` (Array[String]) - Keyword filter
- `excluded_keywords` (Array[String]) - Exclusion filter
- `locations` (Array[String]) - Location filter
- `departments` (Array[String]) - Department filter
- `employment_types` (Array[String]) - Employment type filter
- `remote_types` (Array[String]) - Remote type filter
- `seniority_levels` (Array[String]) - Seniority filter
- `notification_method` (String) - Default 'email'
- `notification_config` (JSON) - Notification settings
- `last_triggered_at` (DateTime) - Optional
- `trigger_count` (Integer) - Default 0
- `created_at` (DateTime) - Auto-generated
- `updated_at` (DateTime) - Auto-updated

**Relationships:**
- `user` → Many-to-one with User
- `notifications` → One-to-many with AlertNotification

**Methods:**
- `matches_position(position)` - Check if position matches alert criteria

**Properties:**
- `immediate_notification` - Check if immediate notifications enabled
- `digest_enabled` - Check if daily digest enabled

---

### 6. UserJobApplication Model (`user_job_application.py`)

**Table:** `user_job_applications`

**Fields:**
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users, indexed
- `job_position_id` (UUID) - Foreign key to job_positions, indexed
- `status` (String) - interested/applied/interviewing/offered/accepted/rejected/withdrawn, indexed
- `applied_at` (DateTime) - Optional
- `notes` (Text) - Optional
- `created_at` (DateTime) - Auto-generated
- `updated_at` (DateTime) - Auto-updated

**Relationships:**
- `user` → Many-to-one with User
- `job_position` → Many-to-one with JobPosition

**Constraints:**
- Unique constraint on (user_id, job_position_id)

**Indexes:**
- `ix_user_job_applications_user_status` - (user_id, status)

**Properties:**
- `is_active` - Check if application is active
- `is_closed` - Check if application is closed

---

### 7. AlertNotification Model (`alert_notification.py`)

**Table:** `alert_notifications`

**Fields:**
- `id` (UUID) - Primary key
- `alert_id` (UUID) - Foreign key to alerts, indexed
- `job_position_id` (UUID) - Foreign key to job_positions, indexed
- `user_id` (UUID) - Foreign key to users, indexed
- `sent_at` (DateTime) - Auto-generated, indexed
- `delivery_status` (String) - pending/sent/delivered/failed/bounced, indexed
- `delivery_method` (String) - email/sms/push/webhook
- `error_message` (Text) - Optional
- `retry_count` (Integer) - Default 0
- `last_retry_at` (DateTime) - Optional

**Relationships:**
- `alert` → Many-to-one with Alert
- `job_position` → Many-to-one with JobPosition
- `user` → Many-to-one with User

**Indexes:**
- `ix_alert_notifications_user_sent` - (user_id, sent_at)
- `ix_alert_notifications_alert_sent` - (alert_id, sent_at)
- `ix_alert_notifications_status_sent` - (delivery_status, sent_at)

**Properties:**
- `is_successful` - Check if notification was delivered
- `is_failed` - Check if notification failed
- `can_retry` - Check if notification can be retried

---

## Database Schema Relationships

```
users (1) ----< (many) alerts
users (1) ----< (many) user_job_applications
users (1) ----< (many) alert_notifications

companies (1) ----< (many) job_positions

job_positions (many) >---- (1) companies
job_positions (1) ----< (many) user_job_applications
job_positions (1) ----< (many) alert_notifications

alerts (many) >---- (1) users
alerts (1) ----< (many) alert_notifications

user_job_applications (many) >---- (1) users
user_job_applications (many) >---- (1) job_positions

alert_notifications (many) >---- (1) alerts
alert_notifications (many) >---- (1) job_positions
alert_notifications (many) >---- (1) users
```

---

## Key Features

### ✅ UUID Primary Keys
- All models use UUID v4 for primary keys
- Better for distributed systems
- No sequential ID leakage

### ✅ Automatic Timestamps
- `created_at` and `updated_at` on all models
- Server-side defaults for consistency
- Timezone-aware datetimes

### ✅ JSON Fields
- Flexible storage for configuration and metadata
- PostgreSQL JSONB for efficient querying
- Used for: preferences, scraping_config, notification_config, salary_range, extra_metadata

### ✅ Array Fields
- PostgreSQL array support for multi-value filters
- Used for: keywords, locations, departments, employment_types, requirements, benefits

### ✅ Indexes
- Strategic indexes on foreign keys
- Composite indexes for common queries
- Status and active flags indexed

### ✅ Relationships
- Proper cascade delete behavior
- Bidirectional relationships
- Lazy loading by default

### ✅ Business Logic
- Helper properties for common operations
- Validation methods (e.g., `matches_position`)
- Status checking methods

---

## Verification

✅ All models imported successfully  
✅ All table names defined correctly  
✅ All relationships defined correctly  
✅ No import errors  
✅ No circular dependencies  

---

## Next Steps

1. **Create database configuration** (`config/database.py`)
2. **Create connection manager** (`src/database/connection.py`)
3. **Initialize Alembic** for migrations
4. **Create initial migration** from models
5. **Apply migration** to create tables
6. **Test CRUD operations**

---

## Files Created/Modified

**Created:**
- ✅ `src/models/user.py`
- ✅ `src/models/alert.py`
- ✅ `src/models/user_job_application.py`
- ✅ `src/models/alert_notification.py`

**Modified:**
- ✅ `src/models/__init__.py` - Added exports for all models
- ✅ `src/models/job_position.py` - Added lifecycle tracking fields

**Existing (Reviewed):**
- ✅ `src/models/base.py` - Base classes and mixins
- ✅ `src/models/company.py` - Company model

---

**Status: Phase 3 Steps 1 & 2 Complete! Ready for database configuration and Alembic setup** 🚀

