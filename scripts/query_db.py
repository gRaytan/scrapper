#!/usr/bin/env python3
"""
Simple script to query the database interactively.
Usage: .venv/bin/python scripts/query_db.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository
from src.storage.repositories.job_repo import JobPositionRepository
from src.utils.logger import logger


def show_all_companies():
    """Show all companies in the database."""
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        companies = company_repo.get_all()
        
        print("\n" + "=" * 100)
        print(f"ALL COMPANIES ({len(companies)} total)")
        print("=" * 100)
        print(f"{'Name':<30} {'Industry':<25} {'Active':<10} {'Last Scraped':<20}")
        print("-" * 100)
        
        for company in companies:
            last_scraped = company.last_scraped_at.strftime("%Y-%m-%d %H:%M") if company.last_scraped_at else "Never"
            active = "✓ Yes" if company.is_active else "✗ No"
            print(f"{company.name:<30} {company.industry or 'N/A':<25} {active:<10} {last_scraped:<20}")
        
        print("=" * 100 + "\n")


def show_active_companies():
    """Show only active companies."""
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        companies = company_repo.get_all(is_active=True)
        
        print("\n" + "=" * 100)
        print(f"ACTIVE COMPANIES ({len(companies)} total)")
        print("=" * 100)
        print(f"{'Name':<30} {'Industry':<25} {'Scraper Type':<15} {'Careers URL':<30}")
        print("-" * 100)
        
        for company in companies:
            scraper_type = company.scraping_config.get('scraper_type', 'N/A') if company.scraping_config else 'N/A'
            careers_url = (company.careers_url[:27] + "...") if len(company.careers_url) > 30 else company.careers_url
            print(f"{company.name:<30} {company.industry or 'N/A':<25} {scraper_type:<15} {careers_url:<30}")
        
        print("=" * 100 + "\n")


def show_company_details(company_name: str):
    """Show detailed information about a specific company."""
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        company = company_repo.get_by_name(company_name)
        
        if not company:
            print(f"\n❌ Company '{company_name}' not found!\n")
            return
        
        print("\n" + "=" * 100)
        print(f"COMPANY DETAILS: {company.name}")
        print("=" * 100)
        print(f"ID:                {company.id}")
        print(f"Website:           {company.website}")
        print(f"Careers URL:       {company.careers_url}")
        print(f"Industry:          {company.industry or 'N/A'}")
        print(f"Size:              {company.size or 'N/A'}")
        print(f"Location:          {company.location or 'N/A'}")
        print(f"Active:            {'Yes' if company.is_active else 'No'}")
        print(f"Scraping Frequency: {company.scraping_frequency}")
        print(f"Last Scraped:      {company.last_scraped_at or 'Never'}")
        print(f"Created:           {company.created_at}")
        print(f"Updated:           {company.updated_at}")
        
        if company.scraping_config:
            print(f"\nScraping Config:")
            for key, value in company.scraping_config.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")
        
        print("=" * 100 + "\n")


def show_job_stats():
    """Show job statistics."""
    with db.get_session() as session:
        job_repo = JobPositionRepository(session)
        
        # Get total jobs
        from sqlalchemy import select, func
        from src.models.job_position import JobPosition
        
        total_jobs = session.execute(
            select(func.count()).select_from(JobPosition)
        ).scalar()
        
        active_jobs = session.execute(
            select(func.count()).select_from(JobPosition).where(JobPosition.is_active == True)
        ).scalar()
        
        print("\n" + "=" * 100)
        print("JOB STATISTICS")
        print("=" * 100)
        print(f"Total Jobs:        {total_jobs}")
        print(f"Active Jobs:       {active_jobs}")
        print(f"Inactive Jobs:     {total_jobs - active_jobs}")
        print("=" * 100 + "\n")


def show_recent_jobs(limit: int = 10):
    """Show most recent jobs."""
    with db.get_session() as session:
        job_repo = JobPositionRepository(session)
        jobs = job_repo.get_recent_jobs(limit=limit)
        
        print("\n" + "=" * 100)
        print(f"RECENT JOBS (Last {limit})")
        print("=" * 100)
        print(f"{'Title':<40} {'Company':<20} {'Location':<20} {'Posted':<15}")
        print("-" * 100)
        
        for job in jobs:
            title = (job.title[:37] + "...") if len(job.title) > 40 else job.title
            company_name = job.company.name if job.company else "Unknown"
            company_name = (company_name[:17] + "...") if len(company_name) > 20 else company_name
            location = (job.location[:17] + "...") if job.location and len(job.location) > 20 else (job.location or "N/A")
            posted = job.posted_date.strftime("%Y-%m-%d") if job.posted_date else "N/A"
            
            print(f"{title:<40} {company_name:<20} {location:<20} {posted:<15}")
        
        print("=" * 100 + "\n")


def show_jobs_by_company(company_name: str, limit: int = 20):
    """Show jobs for a specific company."""
    with db.get_session() as session:
        company_repo = CompanyRepository(session)
        job_repo = JobPositionRepository(session)
        
        company = company_repo.get_by_name(company_name)
        if not company:
            print(f"\n❌ Company '{company_name}' not found!\n")
            return
        
        jobs = job_repo.get_by_company(company.id, is_active=True, limit=limit)
        
        print("\n" + "=" * 100)
        print(f"JOBS AT {company.name} ({len(jobs)} active jobs)")
        print("=" * 100)
        print(f"{'Title':<50} {'Location':<25} {'Department':<20}")
        print("-" * 100)
        
        for job in jobs:
            title = (job.title[:47] + "...") if len(job.title) > 50 else job.title
            location = (job.location[:22] + "...") if job.location and len(job.location) > 25 else (job.location or "N/A")
            department = (job.department[:17] + "...") if job.department and len(job.department) > 20 else (job.department or "N/A")
            
            print(f"{title:<50} {location:<25} {department:<20}")
        
        print("=" * 100 + "\n")


def interactive_menu():
    """Show interactive menu."""
    while True:
        print("\n" + "=" * 100)
        print("DATABASE QUERY TOOL")
        print("=" * 100)
        print("1. Show all companies")
        print("2. Show active companies")
        print("3. Show company details")
        print("4. Show job statistics")
        print("5. Show recent jobs")
        print("6. Show jobs by company")
        print("7. Exit")
        print("=" * 100)
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            show_all_companies()
        elif choice == "2":
            show_active_companies()
        elif choice == "3":
            company_name = input("Enter company name: ").strip()
            show_company_details(company_name)
        elif choice == "4":
            show_job_stats()
        elif choice == "5":
            limit = input("How many jobs to show? (default: 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            show_recent_jobs(limit)
        elif choice == "6":
            company_name = input("Enter company name: ").strip()
            limit = input("How many jobs to show? (default: 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            show_jobs_by_company(company_name, limit)
        elif choice == "7":
            print("\n👋 Goodbye!\n")
            break
        else:
            print("\n❌ Invalid choice. Please try again.\n")


if __name__ == "__main__":
    try:
        # Check if arguments provided
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "companies":
                show_all_companies()
            elif command == "active":
                show_active_companies()
            elif command == "jobs":
                show_job_stats()
            elif command == "recent":
                limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
                show_recent_jobs(limit)
            else:
                print(f"Unknown command: {command}")
                print("\nUsage:")
                print("  .venv/bin/python scripts/query_db.py              # Interactive mode")
                print("  .venv/bin/python scripts/query_db.py companies    # Show all companies")
                print("  .venv/bin/python scripts/query_db.py active       # Show active companies")
                print("  .venv/bin/python scripts/query_db.py jobs         # Show job stats")
                print("  .venv/bin/python scripts/query_db.py recent [N]   # Show N recent jobs")
        else:
            # Interactive mode
            interactive_menu()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

