#!/usr/bin/env python3
"""Script to classify job departments based on job titles.

This script updates jobs with NULL or empty department field by analyzing
their job titles and matching against known patterns.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.models.job_position import JobPosition

# Department patterns - ordered by priority (more specific first)
DEPARTMENT_PATTERNS = {
    # Engineering - specific roles first
    'Software Engineering': [
        'software engineer', 'software developer', 'backend engineer', 'frontend engineer',
        'fullstack engineer', 'full-stack engineer', 'full stack engineer', 'backend developer',
        'frontend developer', 'fullstack developer', 'full-stack developer', 'web developer',
        'application developer', 'mobile developer', 'ios developer', 'android developer',
        'react developer', 'python developer', 'java developer', 'node developer', '.net developer',
        'golang developer', 'go developer', 'rust developer', 'c++ developer', 'c developer',
        'software architect', 'solutions architect', 'principal engineer', 'staff engineer',
        'senior engineer', 'junior developer', 'entry level developer', 'development engineer'
    ],
    'Hardware Engineering': [
        'hardware engineer', 'hardware developer', 'fpga engineer', 'asic engineer',
        'chip designer', 'vlsi engineer', 'embedded engineer', 'embedded developer',
        'firmware engineer', 'firmware developer', 'pcb engineer', 'electrical engineer',
        'electronics engineer', 'rf engineer', 'analog engineer', 'digital design engineer',
        'silicon engineer', 'ic designer', 'verification engineer', 'validation engineer',
        'hardware architect', 'system architect', 'rtl engineer', 'physical design',
        'dft engineer', 'soc engineer', 'chip architect', 'emulation engineer'
    ],
    'DevOps & Infrastructure': [
        'devops', 'sre', 'site reliability', 'platform engineer', 'infrastructure engineer',
        'cloud engineer', 'systems engineer', 'kubernetes', 'docker', 'cicd', 'ci/cd',
        'build engineer', 'release engineer', 'deployment', 'aws engineer', 'azure engineer',
        'gcp engineer', 'linux engineer', 'unix engineer', 'network engineer', 'noc engineer'
    ],
    'Data Engineering': [
        'data engineer', 'data platform', 'etl developer', 'analytics engineer',
        'data architect', 'big data engineer', 'spark engineer', 'data infrastructure',
        'data pipeline', 'database engineer', 'dba', 'database administrator'
    ],
    'Data Science & AI': [
        'data scientist', 'machine learning', 'ml engineer', 'ai engineer', 'research scientist',
        'deep learning', 'nlp engineer', 'computer vision', 'data analyst', 'business intelligence',
        'bi analyst', 'ai researcher', 'ml researcher', 'applied scientist', 'research engineer'
    ],
    'QA & Testing': [
        'qa engineer', 'quality assurance', 'test engineer', 'sdet', 'automation engineer',
        'quality engineer', 'test automation', 'software tester', 'manual tester'
    ],
    'Security': [
        'security engineer', 'security analyst', 'appsec', 'infosec', 'penetration',
        'security researcher', 'cyber security', 'cybersecurity', 'information security',
        'security architect', 'soc analyst', 'threat', 'vulnerability', 'red team', 'blue team'
    ],
    # Product & Design
    'Product Management': [
        'product manager', 'product owner', 'group product manager', 'director of product',
        'vp product', 'head of product', 'chief product', 'product lead', 'product director'
    ],
    'Design': [
        'designer', 'ux designer', 'ui designer', 'product designer', 'graphic designer',
        'visual designer', 'interaction designer', 'ux researcher', 'user researcher',
        'creative director', 'art director', 'brand designer'
    ],
    # Leadership
    'Engineering Management': [
        'engineering manager', 'r&d manager', 'team lead', 'tech lead', 'vp r&d',
        'vp engineering', 'director of engineering', 'head of engineering', 'cto',
        'engineering director', 'development manager', 'r&d director', 'chief technology'
    ],
    # Business Functions
    'Sales': [
        'sales engineer', 'sales representative', 'account executive', 'account manager',
        'sales manager', 'business development', 'bdr', 'sdr', 'sales director',
        'regional sales', 'enterprise sales', 'inside sales', 'field sales'
    ],
    'Marketing': [
        'marketing manager', 'marketing specialist', 'growth', 'content', 'brand',
        'communications', 'digital marketing', 'performance marketing', 'product marketing',
        'demand generation', 'marketing director', 'cmo', 'head of marketing'
    ],
    'HR & People': [
        'recruiter', 'talent acquisition', 'hr ', 'human resources', 'people operations',
        'hr manager', 'hr director', 'compensation', 'benefits', 'payroll',
        'learning and development', 'organizational development', 'hrbp'
    ],
    'Finance & Legal': [
        'finance', 'accountant', 'controller', 'fp&a', 'financial analyst',
        'cfo', 'finance manager', 'tax', 'treasury', 'audit', 'legal', 'counsel',
        'compliance', 'lawyer', 'attorney', 'paralegal', 'contracts'
    ],
    'Customer Success': [
        'customer success', 'client success', 'customer support', 'technical support',
        'support engineer', 'solutions engineer', 'implementation', 'onboarding',
        'customer experience', 'cx', 'client services'
    ],
    'Operations': [
        'operations manager', 'office manager', 'admin', 'procurement', 'logistics',
        'supply chain', 'facilities', 'project manager', 'program manager',
        'business operations', 'strategy and operations', 'chief of staff'
    ],
}


def classify_department(title: str) -> str:
    """Classify a job title into a department."""
    title_lower = title.lower()
    for department, patterns in DEPARTMENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in title_lower:
                return department
    return 'Other'


def main(dry_run: bool = True):
    """Classify jobs with missing departments."""
    with db.get_session() as session:
        # Find jobs without department
        jobs = session.query(JobPosition).filter(
            (JobPosition.department == None) | (JobPosition.department == '')
        ).all()
        
        print(f"Found {len(jobs)} jobs without department classification")
        
        # Classify and count by department
        classifications = {}
        updates = []
        
        for job in jobs:
            new_dept = classify_department(job.title)
            classifications[new_dept] = classifications.get(new_dept, 0) + 1
            if new_dept != 'Other':
                updates.append((job.id, new_dept))
        
        print("\nClassification results:")
        for dept, count in sorted(classifications.items(), key=lambda x: -x[1]):
            print(f"  {dept}: {count}")
        
        print(f"\nTotal jobs that can be classified (not Other): {len(updates)}")
        
        if not dry_run and updates:
            print("\nUpdating database...")
            for job_id, dept in updates:
                session.query(JobPosition).filter(JobPosition.id == job_id).update(
                    {'department': dept}
                )
            session.commit()
            print(f"Updated {len(updates)} jobs")
        elif dry_run:
            print("\n[DRY RUN] No changes made. Run with --apply to update database.")


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    main(dry_run=dry_run)
