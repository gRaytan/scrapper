#!/usr/bin/env python3
"""
Script to migrate companies from YAML configuration to PostgreSQL database.
This is a one-time migration script.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
from config.settings import settings
from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository
from src.utils.logger import logger


def load_companies_from_yaml() -> list:
    """Load companies from YAML configuration file."""
    config_path = settings.base_dir / "config" / "companies.yaml"
    
    logger.info(f"Loading companies from {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    companies = config.get("companies", [])
    logger.info(f"Found {len(companies)} companies in YAML")
    
    return companies


def migrate_companies():
    """Migrate all companies from YAML to database."""
    logger.info("=" * 80)
    logger.info("Starting company migration from YAML to PostgreSQL")
    logger.info("=" * 80)
    
    # Load companies from YAML
    companies_config = load_companies_from_yaml()
    
    # Statistics
    stats = {
        "total": len(companies_config),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Migrate each company
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        
        for company_config in companies_config:
            company_name = company_config.get("name")
            
            try:
                logger.info(f"\nProcessing: {company_name}")
                
                # Check if company already exists
                existing_company = company_repo.get_by_name(company_name)
                
                # Prepare company data
                company_data = {
                    "name": company_name,
                    "website": company_config.get("website"),
                    "careers_url": company_config.get("careers_url"),
                    "industry": company_config.get("industry"),
                    "size": company_config.get("size"),
                    "location": company_config.get("location"),
                    "is_active": company_config.get("is_active", True),
                    "scraping_config": company_config.get("scraping_config", {}),
                    "scraping_frequency": company_config.get("scraping_frequency", "0 0 * * *"),
                }
                
                if existing_company:
                    # Update existing company
                    logger.info(f"  Company exists - updating...")
                    company_repo.update(existing_company.id, company_data)
                    stats["updated"] += 1
                    logger.success(f"  ✓ Updated: {company_name}")
                else:
                    # Create new company
                    logger.info(f"  Creating new company...")
                    company_repo.create(company_data)
                    stats["created"] += 1
                    logger.success(f"  ✓ Created: {company_name}")
                    
            except Exception as e:
                logger.error(f"  ✗ Error processing {company_name}: {e}")
                stats["errors"] += 1
                continue
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total companies:  {stats['total']}")
    logger.info(f"Created:          {stats['created']}")
    logger.info(f"Updated:          {stats['updated']}")
    logger.info(f"Errors:           {stats['errors']}")
    logger.info("=" * 80)
    
    if stats["errors"] == 0:
        logger.success("\n✓ Migration completed successfully!")
    else:
        logger.warning(f"\n⚠ Migration completed with {stats['errors']} errors")
    
    return stats


def verify_migration():
    """Verify that companies were migrated correctly."""
    logger.info("\n" + "=" * 80)
    logger.info("VERIFYING MIGRATION")
    logger.info("=" * 80)
    
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        
        # Get all companies
        all_companies = company_repo.get_all()
        active_companies = company_repo.get_all(is_active=True)
        
        logger.info(f"Total companies in database: {len(all_companies)}")
        logger.info(f"Active companies: {len(active_companies)}")
        
        # List all companies
        logger.info("\nCompanies in database:")
        for company in all_companies:
            status = "✓ ACTIVE" if company.is_active else "✗ INACTIVE"
            logger.info(f"  {status} - {company.name} ({company.industry})")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        # Run migration
        stats = migrate_companies()
        
        # Verify migration
        verify_migration()
        
        # Exit with appropriate code
        sys.exit(0 if stats["errors"] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

