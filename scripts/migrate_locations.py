#!/usr/bin/env python3
"""
Migration script to normalize all job locations in the database.

Usage:
    python scripts/migrate_locations.py --dry-run  # Preview changes
    python scripts/migrate_locations.py            # Apply changes
"""
import argparse
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.location_normalizer import normalize_location
from src.storage.database import db
from src.models.job_position import JobPosition


def migrate_locations(dry_run: bool = True, batch_size: int = 1000):
    """
    Migrate all job locations to normalized format.
    
    Args:
        dry_run: If True, only preview changes without applying
        batch_size: Number of records to process per batch
    """
    print("=" * 70)
    print("LOCATION NORMALIZATION MIGRATION")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be applied)'}")
    print()
    
    with db.get_session() as session:
        # Get all distinct locations
        locations = session.query(
            JobPosition.location,
        ).filter(
            JobPosition.location.isnot(None),
            JobPosition.location != ''
        ).distinct().all()
        
        print(f"Found {len(locations)} distinct locations")
        print()
        
        # Build mapping of old -> new locations
        location_mapping = {}
        changes = defaultdict(list)
        
        for (loc,) in locations:
            normalized = normalize_location(loc)
            if loc != normalized:
                location_mapping[loc] = normalized
                changes[normalized].append(loc)
        
        print(f"Locations to normalize: {len(location_mapping)}")
        print()
        
        # Show changes grouped by normalized value
        print("CHANGES PREVIEW:")
        print("-" * 70)
        for normalized, originals in sorted(changes.items()):
            print(f"\n-> {normalized}")
            for orig in sorted(originals)[:10]:  # Show max 10 examples
                count = session.query(JobPosition).filter(
                    JobPosition.location == orig
                ).count()
                print(f"   {orig} ({count} jobs)")
            if len(originals) > 10:
                print(f"   ... and {len(originals) - 10} more variations")
        
        print()
        print("-" * 70)
        
        if dry_run:
            print("\nDRY RUN - No changes made.")
            print("Run without --dry-run to apply changes.")
            return
        
        # Apply changes
        print("\nApplying changes...")
        total_updated = 0
        
        for old_location, new_location in location_mapping.items():
            updated = session.query(JobPosition).filter(
                JobPosition.location == old_location
            ).update(
                {JobPosition.location: new_location},
                synchronize_session=False
            )
            total_updated += updated
            print(f"  Updated {updated} jobs: '{old_location[:40]}' -> '{new_location}'")
        
        session.commit()
        
        print()
        print("=" * 70)
        print(f"MIGRATION COMPLETE: {total_updated} jobs updated")
        print("=" * 70)


def show_current_stats():
    """Show current location statistics."""
    print("\nCURRENT LOCATION STATISTICS:")
    print("-" * 70)
    
    with db.get_session() as session:
        locations = session.query(
            JobPosition.location,
            db.func.count(JobPosition.id).label('count')
        ).filter(
            JobPosition.location.isnot(None)
        ).group_by(
            JobPosition.location
        ).order_by(
            db.text('count DESC')
        ).limit(30).all()
        
        for loc, count in locations:
            print(f"  {count:>5}  {loc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize job locations in database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current location statistics"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        show_current_stats()
    else:
        migrate_locations(dry_run=args.dry_run)

