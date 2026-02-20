"""Add industry_category column to companies

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j4k5l6m7n8o9'
down_revision: Union[str, None] = 'i3j4k5l6m7n8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Industry to category mapping
INDUSTRY_CATEGORY_MAP = {
    # Technology & Software
    'Technology': 'Technology & Software',
    'Software Development': 'Technology & Software',
    'DevOps': 'Technology & Software',
    'Database': 'Technology & Software',
    'Database / Infrastructure': 'Technology & Software',
    'Web Development / WordPress': 'Technology & Software',
    'Enterprise Software / Cloud Computing / Database': 'Technology & Software',
    'Enterprise Software / ERP': 'Technology & Software',
    'Enterprise Software / IT Service Management': 'Technology & Software',
    'SaaS Management': 'Technology & Software',
    'Technology / Consumer Electronics': 'Technology & Software',
    'Technology / Marketplace': 'Technology & Software',
    'Technology / Semiconductors': 'Technology & Software',
    'Observability': 'Technology & Software',
    'Quality Assurance': 'Technology & Software',
    'Test & Measurement': 'Technology & Software',
    'Networking / Technology Infrastructure': 'Technology & Software',
    
    # Cybersecurity
    'Cybersecurity': 'Cybersecurity',
    'Security': 'Cybersecurity',
    'AI Security': 'Cybersecurity',
    'AI / Security': 'Cybersecurity',
    'Blockchain Security': 'Cybersecurity',
    'IoT Security': 'Cybersecurity',
    'Security Automation': 'Cybersecurity',
    'Cybersecurity / Risk Management': 'Cybersecurity',
    'Compliance': 'Cybersecurity',
    'Data Privacy': 'Cybersecurity',
    
    # AI & Data
    'AI': 'AI & Data',
    'AI / Analytics': 'AI & Data',
    'AI / Automation': 'AI & Data',
    'AI / Chatbot': 'AI & Data',
    'AI / Computer Vision': 'AI & Data',
    'AI / Gaming': 'AI & Data',
    'AI / Low-Code': 'AI & Data',
    'AI / Video': 'AI & Data',
    'AI / Voice Technology': 'AI & Data',
    'Data Analytics': 'AI & Data',
    'Business Intelligence': 'AI & Data',
    'Data Infrastructure': 'AI & Data',
    'Data Intelligence': 'AI & Data',
    'Product Analytics': 'AI & Data',
    'Digital Intelligence / Analytics': 'AI & Data',
    'Document Automation': 'AI & Data',
    
    # FinTech & Finance
    'Financial Technology': 'FinTech & Finance',
    'Financial Technology / Payments': 'FinTech & Finance',
    'Financial Software': 'FinTech & Finance',
    'Banking': 'FinTech & Finance',
    'Insurance': 'FinTech & Finance',
    'Insurance / Insurtech': 'FinTech & Finance',
    'Insurance Technology': 'FinTech & Finance',
    'Venture Capital': 'FinTech & Finance',
    'Gaming / Fintech': 'FinTech & Finance',
    
    # Healthcare & Life Sciences
    'Healthcare Technology': 'Healthcare & Life Sciences',
    'Healthcare AI': 'Healthcare & Life Sciences',
    'Health Tech': 'Healthcare & Life Sciences',
    'Medical Devices': 'Healthcare & Life Sciences',
    'Pharmaceuticals': 'Healthcare & Life Sciences',
    'Biotechnology': 'Healthcare & Life Sciences',
    'Veterinary AI': 'Healthcare & Life Sciences',
    
    # Media & Entertainment
    'Gaming': 'Media & Entertainment',
    'Media Technology': 'Media & Entertainment',
    'Advertising Technology': 'Media & Entertainment',
    'Mobile Advertising': 'Media & Entertainment',
    'Content Discovery / Advertising Technology': 'Media & Entertainment',
    'Publishing': 'Media & Entertainment',
    'Media / Creative': 'Media & Entertainment',
    'Sports Technology': 'Media & Entertainment',
    
    # Hardware & Semiconductors
    'Semiconductors': 'Hardware & Semiconductors',
    'Semiconductors / Infrastructure Software': 'Hardware & Semiconductors',
    'Electronics / Semiconductors': 'Hardware & Semiconductors',
    'Telecommunications': 'Hardware & Semiconductors',
    
    # Retail & E-commerce
    'Retail Technology': 'Retail & E-commerce',
    'Retail Technology / Computer Vision': 'Retail & E-commerce',
    'E-commerce': 'Retail & E-commerce',
    'Consumer Goods': 'Retail & E-commerce',
    
    # Transportation & Logistics
    'Logistics': 'Transportation & Logistics',
    'Mobility': 'Transportation & Logistics',
    'Automotive / LiDAR Technology': 'Transportation & Logistics',
    'Electric Vehicle': 'Transportation & Logistics',
    'Drone Technology': 'Transportation & Logistics',
    'Travel Technology': 'Transportation & Logistics',
    'Aerospace / Defense': 'Transportation & Logistics',
    'Location Technology': 'Transportation & Logistics',
    
    # Energy & Utilities
    'Utilities / Energy': 'Energy & Utilities',
    'Clean Energy': 'Energy & Utilities',
    'Energy': 'Energy & Utilities',
    
    # HR & Professional Services
    'Recruiting': 'HR & Professional Services',
    'HR Technology': 'HR & Professional Services',
    'Professional Services': 'HR & Professional Services',
    'Staffing / Remote Work': 'HR & Professional Services',
    
    # Real Estate & Construction
    'Real Estate Technology': 'Real Estate & Construction',
    'Construction Technology': 'Real Estate & Construction',
    'Hospitality': 'Real Estate & Construction',
    
    # Marketing & Sales
    'Marketing': 'Marketing & Sales',
    'Sales Intelligence / B2B Data': 'Marketing & Sales',
    'Revenue Intelligence / Sales Tech': 'Marketing & Sales',
    
    # Education
    'Education / Training': 'Education',
    
    # Agriculture
    'Agriculture Technology': 'Agriculture',
    
    # Other
    'Unknown': 'Other',
    'Accessibility': 'Other',
    'Cannabis': 'Other',
    'Emergency Services': 'Other',
}


def upgrade() -> None:
    # Add industry_category column
    op.add_column('companies', sa.Column('industry_category', sa.String(100), nullable=True))
    
    # Create index for faster filtering
    op.create_index('ix_companies_industry_category', 'companies', ['industry_category'])
    
    # Update existing records based on mapping
    connection = op.get_bind()
    
    for industry, category in INDUSTRY_CATEGORY_MAP.items():
        connection.execute(
            sa.text(
                "UPDATE companies SET industry_category = :category WHERE industry = :industry"
            ),
            {"category": category, "industry": industry}
        )
    
    # Set any remaining NULL industry_category to 'Other'
    connection.execute(
        sa.text(
            "UPDATE companies SET industry_category = 'Other' WHERE industry_category IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_index('ix_companies_industry_category', table_name='companies')
    op.drop_column('companies', 'industry_category')

