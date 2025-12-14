#!/usr/bin/env python3
"""
Sync LinkedIn-only companies between the YAML config file and the database.

This script can:
1. Export all LinkedIn-only companies from DB to YAML (--export)
2. Import companies from YAML to DB (--import)
3. Show diff between YAML and DB (--diff)

Usage:
    python scripts/sync_linkedin_companies.py --export  # DB -> YAML
    python scripts/sync_linkedin_companies.py --import  # YAML -> DB
    python scripts/sync_linkedin_companies.py --diff    # Show differences
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from src.storage.database import db
from src.models.company import Company


CONFIG_FILE = Path(__file__).parent.parent / "config" / "linkedin_only_companies.yaml"


def load_yaml_companies() -> list[dict]:
    """Load companies from YAML config file."""
    if not CONFIG_FILE.exists():
        return []
    
    with open(CONFIG_FILE, 'r') as f:
        data = yaml.safe_load(f)
    
    return data.get('companies', []) if data else []


def save_yaml_companies(companies: list[dict]):
    """Save companies to YAML config file."""
    # Group by industry
    by_industry = {}
    for c in companies:
        industry = c.get('industry', 'Unknown')
        if industry not in by_industry:
            by_industry[industry] = []
        by_industry[industry].append(c)
    
    # Build ordered list
    ordered_companies = []
    for industry in sorted(by_industry.keys()):
        for c in sorted(by_industry[industry], key=lambda x: x['name']):
            ordered_companies.append(c)
    
    data = {
        'companies': ordered_companies
    }
    
    # Write with header comment
    with open(CONFIG_FILE, 'w') as f:
        f.write("# LinkedIn-Only Companies\n")
        f.write("# These companies are tracked via LinkedIn scraping only (no dedicated career page scraper)\n")
        f.write("# They will be automatically scraped by the scrape_linkedin_jobs_by_company task\n")
        f.write("#\n")
        f.write("# To add a new company, add it to this file and run:\n")
        f.write("#   python scripts/sync_linkedin_companies.py --import\n")
        f.write("#\n")
        f.write("# To export all LinkedIn-only companies from DB to this file:\n")
        f.write("#   python scripts/sync_linkedin_companies.py --export\n\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def get_db_companies() -> list[dict]:
    """Get all LinkedIn-only companies from database."""
    with db.get_session() as session:
        companies = session.query(Company).filter(
            Company.is_active == False
        ).order_by(Company.name).all()
        
        return [
            {
                'name': c.name,
                'website': c.website,
                'industry': c.industry or 'Unknown'
            }
            for c in companies
        ]


def export_to_yaml():
    """Export all LinkedIn-only companies from DB to YAML."""
    companies = get_db_companies()
    save_yaml_companies(companies)
    print(f"Exported {len(companies)} companies to {CONFIG_FILE}")


def import_from_yaml():
    """Import companies from YAML to DB."""
    yaml_companies = load_yaml_companies()
    
    added = 0
    updated = 0
    
    with db.get_session() as session:
        for c in yaml_companies:
            # Ensure name is a string (YAML may parse numeric names like "888" as integers)
            company_name = str(c['name'])
            existing = session.query(Company).filter(
                Company.name.ilike(company_name)
            ).first()
            
            if existing:
                # Update if needed
                if existing.industry != c.get('industry'):
                    existing.industry = c.get('industry', 'Unknown')
                    updated += 1
            else:
                # Add new company
                company = Company(
                    name=company_name,
                    website=c.get('website', ''),
                    careers_url=c.get('careers_url', ''),
                    industry=c.get('industry', 'Unknown'),
                    is_active=True,
                    location='Israel',
                    scraping_config={}
                )
                session.add(company)
                added += 1
        
        session.commit()
    
    print(f"Added {added} new companies, updated {updated} companies")


def show_diff():
    """Show differences between YAML and DB."""
    yaml_companies = {c['name'].lower(): c for c in load_yaml_companies()}
    db_companies = {c['name'].lower(): c for c in get_db_companies()}
    
    yaml_only = set(yaml_companies.keys()) - set(db_companies.keys())
    db_only = set(db_companies.keys()) - set(yaml_companies.keys())
    
    print(f"Companies in YAML only ({len(yaml_only)}):")
    for name in sorted(yaml_only):
        print(f"  + {yaml_companies[name]['name']}")
    
    print(f"\nCompanies in DB only ({len(db_only)}):")
    for name in sorted(db_only):
        print(f"  - {db_companies[name]['name']}")
    
    print(f"\nTotal: {len(yaml_companies)} in YAML, {len(db_companies)} in DB")


def main():
    parser = argparse.ArgumentParser(description="Sync LinkedIn-only companies")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--export', action='store_true', help='Export DB to YAML')
    group.add_argument('--import', dest='import_yaml', action='store_true', help='Import YAML to DB')
    group.add_argument('--diff', action='store_true', help='Show differences')
    
    args = parser.parse_args()
    
    if args.export:
        export_to_yaml()
    elif args.import_yaml:
        import_from_yaml()
    elif args.diff:
        show_diff()


if __name__ == '__main__':
    main()

