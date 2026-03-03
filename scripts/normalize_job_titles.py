#!/usr/bin/env python3
"""
Script to normalize job titles for better filtering and analytics.

This script:
1. Extracts seniority levels from titles
2. Normalizes synonyms (Engineer/Developer, Backend/Back End, etc.)
3. Removes company-specific suffixes and tech stack details
4. Creates canonical normalized titles

Example transformations:
- "Senior Backend Engineer - AI Framework (Python)" → "Senior Backend Engineer"
- "Full-Stack Developer" → "Full Stack Engineer"
- "Team Leads" → "Team Lead"
- "Python Backend Developer" → "Backend Engineer"
"""
import sys
import re
from pathlib import Path
from typing import Tuple, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.models.job_position import JobPosition

# ============================================================================
# Normalization Rules
# ============================================================================

# Seniority levels to extract (in order of precedence)
# NOTE: Staff and Senior are DIFFERENT levels - Staff is higher than Senior
SENIORITY_LEVELS = [
    'Chief', 'C-Level', 'VP', 'Vice President',
    'Director', 'Head of', 'Principal', 'Distinguished',
    'Staff',  # Staff is higher than Senior
    'Senior', 'Sr', 'Sr.',  # Senior level
    'Mid-Level', 'Mid', 'Intermediate',
    'Junior', 'Jr', 'Jr.', 'Entry Level', 'Entry-Level', 'Associate'
]

# Seniority normalization (map variations to standard form)
SENIORITY_MAPPING = {
    'Sr': 'Senior',
    'Sr.': 'Senior',
    'Jr': 'Junior',
    'Jr.': 'Junior',
    'Entry Level': 'Junior',
    'Entry-Level': 'Junior',
    'Associate': 'Junior',
    'Mid-Level': 'Mid',
    'Intermediate': 'Mid',
    'Vice President': 'VP',
    'C-Level': 'Executive',
    'Chief': 'Executive',
}

# Synonym mappings (normalize to preferred term)
SYNONYM_MAPPING = {
    # Engineer vs Developer
    'Developer': 'Engineer',
    'Dev': 'Engineer',
    'Programmer': 'Engineer',

    # Backend variations
    'Back End': 'Backend',
    'Back-End': 'Backend',

    # Frontend variations
    'Front End': 'Frontend',
    'Front-End': 'Frontend',

    # Full Stack variations
    'Fullstack': 'Full Stack',
    'Full-Stack': 'Full Stack',
    'Full-stack': 'Full Stack',

    # Team Lead variations (NOT Tech Lead - they are different)
    'Team Leader': 'Team Lead',

    # Tech Lead variations (separate from Team Lead)
    'Technical Lead': 'Tech Lead',
    'TL': 'Tech Lead',

    # Manager variations
    'Mgr': 'Manager',
    'Mngr': 'Manager',

    # Architect variations
    'Solutions Architect': 'Architect',

    # Data variations
    'Data Science': 'Data Scientist',
    'ML Engineer': 'Machine Learning Engineer',
    # AI Engineer is kept separate - NOT mapped to ML Engineer
}

# Patterns to remove (company codes, locations, tech stacks, etc.)
REMOVAL_PATTERNS = [
    r'\s*-\s*[A-Z][a-z]+\s*\d+',  # e.g., "- Base44"
    r'\s*-\s*[A-Z]{2,}',  # e.g., "- ISR", "- EU"
    r'\s*\([^)]*\)',  # Remove anything in parentheses
    r'\s*-\s*.*Team$',  # e.g., "- GenAI Team"
    r'\s*-\s*.*Platform$',  # e.g., "- Securities Platform"
    r'\s*,\s*.*$',  # Remove everything after comma
    r'\s+JB-\d+',  # Job codes like "JB-26693"
    r'\s+\d{4,}',  # Job codes like "7225"
]

# Tech stack keywords to remove from base title
TECH_STACK_KEYWORDS = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang', 'Rust',
    'C\\+\\+', 'C#', '\\.NET', 'Node\\.js', 'React', 'Angular', 'Vue',
    'AWS', 'Azure', 'GCP', 'Kubernetes', 'Docker', 'Redis', 'MongoDB',
    'PostgreSQL', 'MySQL', 'Salesforce', 'SAP', 'Oracle',
    'GenAI', 'LLM', 'AI', 'ML', 'Data-Focused', 'Cloud', 'Distributed Systems'
]

# ============================================================================
# Normalization Functions
# ============================================================================

def extract_seniority(title: str) -> Tuple[Optional[str], str]:
    """
    Extract seniority level from title.
    
    Returns:
        Tuple of (seniority_level, title_without_seniority)
    """
    title_lower = title.lower()
    
    for seniority in SENIORITY_LEVELS:
        seniority_lower = seniority.lower()
        # Match at word boundaries
        pattern = r'\b' + re.escape(seniority_lower) + r'\b'
        if re.search(pattern, title_lower):
            # Remove seniority from title
            title_without = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
            # Normalize seniority
            normalized_seniority = SENIORITY_MAPPING.get(seniority, seniority)
            return normalized_seniority, title_without
    
    return None, title


def remove_company_suffixes(title: str) -> str:
    """Remove company-specific suffixes and codes."""
    for pattern in REMOVAL_PATTERNS:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    return title.strip()


def remove_tech_stack(title: str) -> str:
    """Remove tech stack keywords from title."""
    for tech in TECH_STACK_KEYWORDS:
        # Match at word boundaries
        pattern = r'\b' + tech + r'\b'
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    # Clean up extra spaces and dashes
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\s*-\s*$', '', title)
    title = re.sub(r'^\s*-\s*', '', title)
    return title.strip()


def normalize_synonyms(title: str) -> str:
    """Normalize synonyms to preferred terms."""
    for synonym, preferred in SYNONYM_MAPPING.items():
        # Match at word boundaries
        pattern = r'\b' + re.escape(synonym) + r'\b'
        title = re.sub(pattern, preferred, title, flags=re.IGNORECASE)
    return title


def singularize(title: str) -> str:
    """Convert plural forms to singular."""
    # Simple pluralization rules
    replacements = [
        (r'\bLeads\b', 'Lead'),
        (r'\bManagers\b', 'Manager'),
        (r'\bEngineers\b', 'Engineer'),
        (r'\bDevelopers\b', 'Engineer'),  # Also normalize to Engineer
        (r'\bArchitects\b', 'Architect'),
        (r'\bAnalysts\b', 'Analyst'),
        (r'\bDesigners\b', 'Designer'),
        (r'\bScientists\b', 'Scientist'),
    ]

    for pattern, replacement in replacements:
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)

    return title


def normalize_title(title: str) -> str:
    """
    Main normalization function.

    Steps:
    1. Remove company suffixes and codes
    2. Extract seniority level
    3. Remove tech stack keywords
    4. Normalize synonyms
    5. Singularize
    6. Clean up whitespace
    7. Reconstruct with seniority
    """
    if not title:
        return ""

    # Step 1: Remove company suffixes
    title = remove_company_suffixes(title)

    # Step 2: Extract seniority
    seniority, base_title = extract_seniority(title)

    # Step 3: Remove tech stack
    base_title = remove_tech_stack(base_title)

    # Step 4: Normalize synonyms
    base_title = normalize_synonyms(base_title)

    # Step 5: Singularize
    base_title = singularize(base_title)

    # Step 6: Clean up whitespace and extra characters
    base_title = re.sub(r'\s+', ' ', base_title)
    base_title = re.sub(r'\s*:\s*', ': ', base_title)
    base_title = base_title.strip()

    # Step 7: Reconstruct with seniority
    if seniority:
        return f"{seniority} {base_title}"
    return base_title


# ============================================================================
# Main Script
# ============================================================================

def main(dry_run: bool = True):
    """Run the normalization script."""
    with db.get_session() as session:
        # Get all active jobs
        jobs = session.query(JobPosition).filter(
            JobPosition.is_active == True
        ).all()

        print(f"Found {len(jobs)} active jobs to normalize")

        # Track statistics
        normalized_titles = {}
        examples = {}

        for job in jobs:
            original = job.title
            normalized = normalize_title(original)

            # Track normalized title counts
            if normalized not in normalized_titles:
                normalized_titles[normalized] = 0
                examples[normalized] = []

            normalized_titles[normalized] += 1

            # Keep up to 3 examples per normalized title
            if len(examples[normalized]) < 3 and original != normalized:
                examples[normalized].append(original)

        # Print statistics
        print(f"\n{'='*80}")
        print(f"NORMALIZATION RESULTS")
        print(f"{'='*80}")
        print(f"Original unique titles: 4504")
        print(f"Normalized unique titles: {len(normalized_titles)}")
        print(f"Reduction: {4504 - len(normalized_titles)} titles ({((4504 - len(normalized_titles)) / 4504 * 100):.1f}%)")

        # Show top 30 normalized titles
        print(f"\n{'='*80}")
        print(f"TOP 30 NORMALIZED TITLES")
        print(f"{'='*80}")
        sorted_titles = sorted(normalized_titles.items(), key=lambda x: -x[1])
        for i, (title, count) in enumerate(sorted_titles[:30], 1):
            print(f"{i:2d}. {title:50s} ({count:3d} jobs)")
            if title in examples and examples[title]:
                for example in examples[title][:2]:
                    print(f"    Example: {example}")

        if not dry_run:
            print(f"\n{'='*80}")
            print(f"UPDATING DATABASE")
            print(f"{'='*80}")

            updated = 0
            for job in jobs:
                normalized = normalize_title(job.title)
                if normalized != job.title:
                    job.normalized_title = normalized
                    updated += 1

            session.commit()
            print(f"✅ Updated {updated} jobs with normalized titles")
        else:
            print(f"\n{'='*80}")
            print(f"[DRY RUN] No changes made. Run with --apply to update database.")
            print(f"{'='*80}")


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    main(dry_run=dry_run)

