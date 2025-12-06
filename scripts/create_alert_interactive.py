#!/usr/bin/env python3
"""
Interactive script to create alerts via API.
Helps you create an alert for Engineering Manager positions at Meta.
"""
import sys
from pathlib import Path
import requests
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository
from src.utils.logger import logger


def get_meta_company_id():
    """Get Meta's company ID from the database."""
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        meta_company = company_repo.get_by_name("Meta")
        
        if not meta_company:
            logger.error("❌ Meta company not found in database!")
            logger.info("Please run: python scripts/migrate_companies_to_db.py")
            return None
        
        return str(meta_company.id)


def create_alert_via_api(base_url: str, access_token: str, company_id: str):
    """
    Create alert via API.
    
    Args:
        base_url: API base URL (e.g., http://localhost:8000)
        access_token: JWT access token
        company_id: Meta company UUID
    """
    logger.info("=" * 80)
    logger.info("Creating Alert via API")
    logger.info("=" * 80)
    
    # Prepare alert data
    alert_data = {
        "name": "Engineering Manager - Meta",
        "is_active": True,
        "company_ids": [company_id],
        "keywords": ["engineering manager", "manager, engineering", "eng manager"],
        "excluded_keywords": [],
        "locations": [],
        "departments": [],
        "employment_types": [],
        "remote_types": [],
        "seniority_levels": [],
        "notification_method": "email",
        "notification_config": {
            "frequency": "immediate"
        }
    }
    
    # Make API request
    url = f"{base_url}/api/v1/alerts/users/me/alerts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"POST {url}")
    logger.info(f"Alert Data: {json.dumps(alert_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=alert_data)
        
        if response.status_code == 201:
            alert = response.json()
            logger.success("✅ Alert created successfully!")
            logger.info(f"\nAlert Details:")
            logger.info(f"  ID: {alert['id']}")
            logger.info(f"  Name: {alert['name']}")
            logger.info(f"  Company IDs: {alert['company_ids']}")
            logger.info(f"  Keywords: {alert['keywords']}")
            logger.info(f"  Active: {alert['is_active']}")
            logger.info(f"  Created: {alert['created_at']}")
            
            # Test the alert
            logger.info("\n" + "=" * 80)
            logger.info("Testing Alert")
            logger.info("=" * 80)
            
            test_url = f"{base_url}/api/v1/alerts/alerts/{alert['id']}/test"
            test_response = requests.post(test_url, headers=headers, params={"limit": 5})
            
            if test_response.status_code == 200:
                test_result = test_response.json()
                logger.info(f"Matching jobs: {test_result['matching_jobs_count']}")
                logger.info(f"Total active jobs: {test_result['total_active_jobs']}")
                
                if test_result['sample_jobs']:
                    logger.info("\n📋 Sample Matching Jobs:")
                    for i, job in enumerate(test_result['sample_jobs'], 1):
                        logger.info(f"\n{i}. {job['title']}")
                        logger.info(f"   Company: {job['company']['name']}")
                        logger.info(f"   Location: {job['location']}")
                else:
                    logger.warning("⚠️  No matching jobs found currently.")
            
            return alert
        else:
            logger.error(f"❌ Failed to create alert: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None


def print_curl_command(company_id: str):
    """Print curl command to create the alert."""
    logger.info("\n" + "=" * 80)
    logger.info("Alternative: Create Alert using curl")
    logger.info("=" * 80)
    
    curl_cmd = f"""
curl -X POST http://localhost:8000/api/v1/alerts/users/me/alerts \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "name": "Engineering Manager - Meta",
    "is_active": true,
    "company_ids": ["{company_id}"],
    "keywords": ["engineering manager", "manager, engineering", "eng manager"],
    "excluded_keywords": [],
    "locations": [],
    "departments": [],
    "employment_types": [],
    "remote_types": [],
    "seniority_levels": [],
    "notification_method": "email",
    "notification_config": {{"frequency": "immediate"}}
  }}'
"""
    
    logger.info(curl_cmd)


if __name__ == "__main__":
    # Get Meta company ID
    company_id = get_meta_company_id()
    
    if not company_id:
        sys.exit(1)
    
    logger.info(f"✅ Meta Company ID: {company_id}")
    
    # Print curl command
    print_curl_command(company_id)
    
    logger.info("\n" + "=" * 80)
    logger.info("Next Steps:")
    logger.info("=" * 80)
    logger.info("1. Start the API server: python3 -m uvicorn src.api.app:app --reload --port 8000")
    logger.info("2. Login to get access token: POST /api/v1/auth/login")
    logger.info("3. Use the curl command above (replace YOUR_ACCESS_TOKEN)")
    logger.info("\nOr run this script with your access token:")
    logger.info("   python scripts/create_alert_interactive.py <access_token>")

