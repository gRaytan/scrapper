#!/usr/bin/env python3
"""
Quick test script for LinkedIn scraping with de-duplication.
"""
import asyncio
from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository
from src.services.company_matching_service import CompanyMatchingService
from src.services.deduplication_service import JobDeduplicationService

def test_company_matching():
    """Test company name matching."""
    print("\n" + "="*80)
    print("Testing Company Matching Service")
    print("="*80)
    
    with db.get_session() as session:
        matcher = CompanyMatchingService(session)
        
        test_cases = [
            "Google",
            "Meta",
            "Facebook",
            "Microsoft Corporation",
            "Wix.com",
            "monday.com",
            "Unknown Startup Ltd"
        ]
        
        for company_name in test_cases:
            matched, confidence = matcher.find_matching_company(company_name)
            if matched:
                print(f"✓ '{company_name}' → '{matched.name}' (confidence: {confidence:.2f})")
            else:
                print(f"✗ '{company_name}' → No match found")

def test_deduplication():
    """Test job de-duplication."""
    print("\n" + "="*80)
    print("Testing De-duplication Service")
    print("="*80)
    
    with db.get_session() as session:
        dedup = JobDeduplicationService(session)
        company_repo = CompanyRepository(session)
        
        # Get a company to test with
        companies = company_repo.get_all(is_active=True)
        if not companies:
            print("No active companies found. Skipping de-duplication test.")
            return
        
        company = companies[0]
        print(f"\nTesting with company: {company.name}")
        
        # Test cases: (title, location)
        test_cases = [
            ("Senior Software Engineer", "Tel Aviv, Israel"),
            ("Software Engineer - Senior", "Tel Aviv"),
            ("Backend Developer", "Herzliya"),
        ]
        
        for title, location in test_cases:
            duplicate, score, needs_review = dedup.check_for_duplicate(
                company_id=str(company.id),
                title=title,
                location=location
            )
            
            if duplicate:
                print(f"\n  Title: '{title}' | Location: '{location}'")
                print(f"  → Duplicate found: '{duplicate.title}' (score: {score:.2f})")
                print(f"  → Needs review: {needs_review}")
            else:
                print(f"\n  Title: '{title}' | Location: '{location}'")
                print(f"  → No duplicate found")

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("LinkedIn Integration Test Suite")
    print("="*80)
    
    try:
        test_company_matching()
        test_deduplication()
        
        print("\n" + "="*80)
        print("✓ All tests completed successfully!")
        print("="*80)
        print("\nTo run LinkedIn scraping manually:")
        print("  python3 -c \"from src.workers.tasks import scrape_linkedin_jobs; scrape_linkedin_jobs(keywords='Software Engineer', location='Israel', max_pages=2)\"")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

