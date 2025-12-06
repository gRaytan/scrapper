#!/usr/bin/env python3
"""
Script to retrieve ALL jobs matching a specific alert.
Unlike the test_alert endpoint which returns limited samples, this returns all matches.
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.storage.repositories.alert_repo import AlertRepository
from src.models.job_position import JobPosition
from sqlalchemy.orm import joinedload
from src.utils.logger import logger


def get_all_matching_jobs(alert_id: str, export_json: bool = False):
    """
    Get ALL jobs matching an alert.
    
    Args:
        alert_id: Alert UUID
        export_json: Whether to export results to JSON file
    """
    logger.info("=" * 80)
    logger.info("Retrieving All Jobs Matching Alert")
    logger.info("=" * 80)
    
    with db.get_session() as session:
        # Get alert
        alert_repo = AlertRepository(session)
        alert = alert_repo.get_by_id(alert_id)
        
        if not alert:
            logger.error(f"❌ Alert not found: {alert_id}")
            return None
        
        logger.info(f"✅ Found Alert: {alert.name}")
        logger.info(f"   User ID: {alert.user_id}")
        logger.info(f"   Active: {alert.is_active}")
        logger.info(f"   Company IDs: {alert.company_ids}")
        logger.info(f"   Keywords: {alert.keywords}")
        logger.info(f"   Excluded Keywords: {alert.excluded_keywords}")
        logger.info(f"   Locations: {alert.locations or 'All'}")
        logger.info(f"   Departments: {alert.departments or 'All'}")
        
        # Get all active jobs
        logger.info("\n📊 Querying database for active jobs...")
        active_jobs = session.query(JobPosition).filter(
            JobPosition.is_active == True
        ).options(joinedload(JobPosition.company)).all()
        
        logger.info(f"   Total active jobs in database: {len(active_jobs)}")
        
        # Find ALL matching jobs
        logger.info("\n🔍 Filtering jobs by alert criteria...")
        matching_jobs = []
        for job in active_jobs:
            if alert.matches_position(job):
                matching_jobs.append(job)
        
        logger.success(f"\n✅ Found {len(matching_jobs)} matching jobs!")
        
        # Display results
        if matching_jobs:
            logger.info("\n" + "=" * 80)
            logger.info("Matching Jobs")
            logger.info("=" * 80)
            
            for i, job in enumerate(matching_jobs, 1):
                logger.info(f"\n{i}. {job.title}")
                logger.info(f"   Company: {job.company.name}")
                logger.info(f"   Location: {job.location}")
                logger.info(f"   Department: {job.department or 'N/A'}")
                logger.info(f"   Posted: {job.posted_date or 'N/A'}")
                logger.info(f"   URL: {job.job_url}")
                logger.info(f"   External ID: {job.external_id}")
                logger.info(f"   Remote: {job.is_remote}")
        
        # Export to JSON if requested
        if export_json:
            export_data = {
                "alert": {
                    "id": str(alert.id),
                    "name": alert.name,
                    "user_id": str(alert.user_id),
                    "company_ids": [str(cid) for cid in alert.company_ids] if alert.company_ids else [],
                    "keywords": alert.keywords or [],
                    "excluded_keywords": alert.excluded_keywords or [],
                    "locations": alert.locations or [],
                    "departments": alert.departments or [],
                },
                "results": {
                    "total_active_jobs": len(active_jobs),
                    "matching_jobs_count": len(matching_jobs),
                    "retrieved_at": datetime.utcnow().isoformat(),
                },
                "jobs": [
                    {
                        "id": str(job.id),
                        "title": job.title,
                        "company": {
                            "id": str(job.company.id),
                            "name": job.company.name,
                        },
                        "location": job.location,
                        "department": job.department,
                        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                        "job_url": job.job_url,
                        "external_id": job.external_id,
                        "is_remote": job.is_remote,
                        "employment_type": job.employment_type,
                        "description": job.description[:500] + "..." if job.description and len(job.description) > 500 else job.description,
                    }
                    for job in matching_jobs
                ]
            }
            
            filename = f"alert_matches_{alert_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = Path("data/exports") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.success(f"\n✅ Exported to: {filepath}")
        
        return {
            "alert": alert,
            "matching_jobs": matching_jobs,
            "total_active_jobs": len(active_jobs),
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python scripts/get_alert_matching_jobs.py <alert_id> [--export-json]")
        logger.info("\nExample:")
        logger.info("  python scripts/get_alert_matching_jobs.py 123e4567-e89b-12d3-a456-426614174000")
        logger.info("  python scripts/get_alert_matching_jobs.py 123e4567-e89b-12d3-a456-426614174000 --export-json")
        sys.exit(1)
    
    alert_id = sys.argv[1]
    export_json = "--export-json" in sys.argv
    
    try:
        result = get_all_matching_jobs(alert_id, export_json=export_json)
        if result:
            logger.success(f"\n✅ Successfully retrieved {len(result['matching_jobs'])} matching jobs!")
            sys.exit(0)
        else:
            logger.error("\n❌ Failed to retrieve matching jobs!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.exception(e)
        sys.exit(1)

