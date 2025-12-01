#!/usr/bin/env python3
"""
Script to update company active status in the database.
Usage: .venv/bin/python scripts/update_company_status.py "Company Name" false
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository
from src.utils.logger import logger


def update_company_status(company_name: str, is_active: bool):
    """Update company active status."""
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        
        # Get company
        company = company_repo.get_by_name(company_name)
        
        if not company:
            logger.error(f"Company '{company_name}' not found in database!")
            return False
        
        # Update status
        logger.info(f"Updating {company_name}: is_active = {is_active}")
        company_repo.update(company.id, {"is_active": is_active})
        
        logger.success(f"✓ Updated {company_name} to {'ACTIVE' if is_active else 'INACTIVE'}")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: .venv/bin/python scripts/update_company_status.py \"Company Name\" <true|false>")
        print("\nExample:")
        print("  .venv/bin/python scripts/update_company_status.py \"Check Point\" false")
        sys.exit(1)
    
    company_name = sys.argv[1]
    is_active_str = sys.argv[2].lower()
    
    if is_active_str not in ["true", "false"]:
        print("Error: Status must be 'true' or 'false'")
        sys.exit(1)
    
    is_active = is_active_str == "true"
    
    success = update_company_status(company_name, is_active)
    sys.exit(0 if success else 1)

