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
# These are applied in order - more specific patterns first
REMOVAL_PATTERNS = [
    # Remove everything after comma (specializations, locations, etc.)
    r',\s*.*$',  # e.g., ", Network Management", ", Bangkok Based"

    # Remove everything in parentheses (tech stacks, codes, locations)
    r'\s*\([^)]*\)',  # e.g., "(Python)", "(AWS)", "(23743)", "(Bangkok-based)"

    # Remove everything after dash (specializations, teams, products)
    r'\s*-\s*.*$',  # e.g., "- Security", "- GenAI Team", "- Base44", "- Cortex XSIAM"

    # Remove job codes (various formats)
    r'\s+JB-\d+',  # e.g., "JB-26693"
    r'\s+\d{4,}',  # e.g., "7225", "237489"
    r'\s+#\d+',  # e.g., "#1234"
]

# Tech stack keywords to remove from base title (before other removals)
TECH_STACK_KEYWORDS = [
    # Programming languages
    'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang', 'Rust',
    'C\\+\\+', 'C#', '\\.NET', 'Node\\.js', 'Ruby', 'PHP', 'Scala', 'Kotlin',

    # Frontend frameworks
    'React', 'Angular', 'Vue', 'Svelte', 'Next\\.js', 'Nuxt',

    # Cloud & Infrastructure
    'AWS', 'Azure', 'GCP', 'Google Cloud', 'Kubernetes', 'K8s', 'Docker',
    'Terraform', 'Ansible', 'Jenkins', 'CI/CD',

    # Databases
    'Redis', 'MongoDB', 'PostgreSQL', 'MySQL', 'Cassandra', 'DynamoDB',
    'Elasticsearch', 'SQL', 'NoSQL',

    # Enterprise software
    'Salesforce', 'SAP', 'Oracle', 'ServiceNow', 'Workday',

    # AI/ML (but keep "AI Engineer" and "ML Engineer" as roles)
    'GenAI', 'LLM', 'NLP', 'Data-Focused', 'Deep Learning',

    # Other tech terms
    'Cloud', 'Distributed Systems', 'Microservices', 'API', 'REST',
    'GraphQL', 'Kafka', 'RabbitMQ', 'gRPC',
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
        # Match at word boundaries, including optional period and space after abbreviations
        # This handles "Sr. Engineer", "Sr Engineer", "Senior Engineer" all correctly
        pattern = r'\b' + re.escape(seniority_lower) + r'\.?\s*'
        if re.search(pattern, title_lower):
            # Remove seniority from title (including optional period and space)
            title_without = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
            # Clean up any leftover periods or multiple spaces
            title_without = re.sub(r'^\.\s*', '', title_without)
            title_without = re.sub(r'\s+', ' ', title_without).strip()
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
    Balanced normalization function.

    Steps:
    1. Remove content in parentheses (team names, codes, etc.)
    2. Remove suffixes after dash (team names, locations, etc.)
    3. Normalize seniority abbreviations (Sr. → Senior, Jr. → Junior)
    4. Normalize common synonyms (Developer → Engineer, Back End → Backend)
    5. Clean up whitespace
    """
    if not title:
        return ""

    # Step 1: Remove content in parentheses
    # Examples: "(Falcon Cloud Security)", "(24410)", "(BigBrain)"
    title = re.sub(r'\s*\([^)]*\)', '', title)

    # Step 2: Remove suffixes after dash (but keep core role descriptions)
    # Remove team names, locations, and other context after dash
    # Examples: "- CWPP Team", "- Israel", "- JFrog Security"
    # But keep things like "Full-Stack" or "Back-End"
    title = re.sub(r'\s*[-–]\s+[A-Z][^-]*$', '', title)

    # Step 3: Normalize seniority abbreviations in place
    # Replace Sr. with Senior, Jr. with Junior, etc.
    for seniority in SENIORITY_LEVELS:
        if seniority in ['Sr', 'Sr.']:
            # Match Sr. or Sr followed by space
            pattern = r'\bSr\.?\s+'
            title = re.sub(pattern, 'Senior ', title, flags=re.IGNORECASE)
        elif seniority in ['Jr', 'Jr.']:
            pattern = r'\bJr\.?\s+'
            title = re.sub(pattern, 'Junior ', title, flags=re.IGNORECASE)
        elif seniority == 'Vice President':
            # Normalize "Vice President" to "VP"
            pattern = r'\bVice President\b'
            title = re.sub(pattern, 'VP', title, flags=re.IGNORECASE)

    # Step 4: Normalize common synonyms
    synonyms = {
        r'\bDeveloper\b': 'Engineer',
        r'\bBack End\b': 'Backend',
        r'\bBack-End\b': 'Backend',
        r'\bFront End\b': 'Frontend',
        r'\bFront-End\b': 'Frontend',
        r'\bFull Stack\b': 'Full Stack',
        r'\bFull-Stack\b': 'Full Stack',
        r'\bFullstack\b': 'Full Stack',
        r'\bDevOps\b': 'DevOps',
        r'\bDev Ops\b': 'DevOps',
        r'\bML\b': 'Machine Learning',
        r'\bAI\b': 'AI',
    }

    for pattern, replacement in synonyms.items():
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)

    # Step 5: Clean up whitespace and trailing punctuation
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[,\-–]+$', '', title)  # Remove trailing commas, dashes
    title = title.strip()

    return title


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
                # Always update normalized_title, even if it's the same as the original
                # This ensures all jobs have a normalized_title value
                if job.normalized_title != normalized:
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

