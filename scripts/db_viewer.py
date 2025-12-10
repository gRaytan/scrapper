#!/usr/bin/env python3
"""
Simple web-based database viewer.
Provides a web interface to view jobs, companies, and scraping sessions.
"""
import sys
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from src.models.company import Company
from src.models.job_position import JobPosition
from src.models.scraping_session import ScrapingSession
from sqlalchemy import func, desc

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Scraper Database Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 30px; }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card .value { font-size: 32px; font-weight: bold; color: #2563eb; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
        }
        .tab {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        .tab:hover { color: #2563eb; }
        .tab.active { color: #2563eb; border-bottom-color: #2563eb; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        table {
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #f9fafb; font-weight: 600; color: #374151; }
        tr:hover { background: #f9fafb; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge.active { background: #dcfce7; color: #166534; }
        .badge.inactive { background: #fee2e2; color: #991b1b; }
        .badge.remote { background: #dbeafe; color: #1e40af; }
        .badge.onsite { background: #fef3c7; color: #92400e; }
        .badge.hybrid { background: #e9d5ff; color: #6b21a8; }
        .badge.linkedin { background: #0077b5; color: white; }
        .badge.company { background: #10b981; color: white; }
        .badge.other { background: #6b7280; color: white; }
        .filters {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filter-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .filter-group label { font-weight: 500; color: #374151; }
        .filter-group select, .filter-group input {
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
        }
        .refresh-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        .refresh-btn:hover { background: #1d4ed8; }
        .job-link { color: #2563eb; text-decoration: none; }
        .job-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Job Scraper Database Viewer</h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Jobs</h3>
                <div class="value" id="total-jobs">{{ stats.total_jobs }}</div>
            </div>
            <div class="stat-card">
                <h3>Active Jobs</h3>
                <div class="value" id="active-jobs">{{ stats.active_jobs }}</div>
            </div>
            <div class="stat-card">
                <h3>Companies</h3>
                <div class="value" id="total-companies">{{ stats.total_companies }}</div>
            </div>
            <div class="stat-card">
                <h3>Active Companies</h3>
                <div class="value" id="active-companies">{{ stats.active_companies }}</div>
            </div>
            <div class="stat-card">
                <h3>Last Scrape</h3>
                <div class="value" style="font-size: 18px;" id="last-scrape">{{ stats.last_scrape }}</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('jobs')">Jobs</button>
            <button class="tab" onclick="showTab('companies')">Companies</button>
            <button class="tab" onclick="showTab('sessions')">Scraping Sessions</button>
        </div>

        <div id="jobs" class="tab-content active">
            <div class="filters">
                <div class="filter-group">
                    <div>
                        <label>Company:</label>
                        <select id="company-filter" onchange="filterJobs()">
                            <option value="">All Companies</option>
                            {% for company in companies %}
                            <option value="{{ company.name }}">{{ company.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Role:</label>
                        <select id="role-filter" onchange="filterJobs()">
                            <option value="">All Roles</option>
                            {% for role in roles %}
                            <option value="{{ role }}">{{ role }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Source:</label>
                        <select id="source-filter" onchange="filterJobs()">
                            <option value="">All Sources</option>
                            <option value="linkedin_aggregator">LinkedIn</option>
                            <option value="company">Company Page</option>
                        </select>
                    </div>
                    <div>
                        <label>Search:</label>
                        <input type="text" id="search-filter" placeholder="Search title..." onkeyup="filterJobs()">
                    </div>
                    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                </div>
            </div>
            
            <table id="jobs-table">
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Title</th>
                        <th>Location</th>
                        <th>Source</th>
                        <th>Department</th>
                        <th>Posted Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="jobs-tbody">
                    {% for job in jobs %}
                    <tr data-company="{{ job.company_name }}" data-title="{{ job.title }}" data-source="{{ job.source_type }}" data-role="{{ job.role }}">
                        <td>{{ job.company_name }}</td>
                        <td><a href="{{ job.job_url }}" target="_blank" class="job-link">{{ job.title }}</a></td>
                        <td>{{ job.location or 'N/A' }}</td>
                        <td>
                            {% if job.source_type == 'linkedin_aggregator' %}
                            <span class="badge linkedin">LinkedIn</span>
                            {% elif job.source_type %}
                            <span class="badge company">Company Page</span>
                            {% else %}
                            <span class="badge other">Other</span>
                            {% endif %}
                        </td>
                        <td>{{ job.department or 'N/A' }}</td>
                        <td>{{ job.posted_date.strftime('%Y-%m-%d') if job.posted_date else 'N/A' }}</td>
                        <td>
                            <span class="badge {{ 'active' if job.is_active else 'inactive' }}">
                                {{ 'Active' if job.is_active else 'Inactive' }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div id="companies" class="tab-content">
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Website</th>
                        <th>Industry</th>
                        <th>Location</th>
                        <th>Jobs Count</th>
                        <th>Last Scraped</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for company in companies_with_stats %}
                    <tr>
                        <td><strong>{{ company.name }}</strong></td>
                        <td><a href="{{ company.website }}" target="_blank" class="job-link">{{ company.website }}</a></td>
                        <td>{{ company.industry or 'N/A' }}</td>
                        <td>{{ company.location or 'N/A' }}</td>
                        <td>{{ company.job_count }}</td>
                        <td>{{ company.last_scraped_at.strftime('%Y-%m-%d %H:%M') if company.last_scraped_at else 'Never' }}</td>
                        <td>
                            <span class="badge {{ 'active' if company.is_active else 'inactive' }}">
                                {{ 'Active' if company.is_active else 'Inactive' }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div id="sessions" class="tab-content">
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Started</th>
                        <th>Duration</th>
                        <th>Found</th>
                        <th>New</th>
                        <th>Updated</th>
                        <th>Removed</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for session in sessions %}
                    <tr>
                        <td>{{ session.company_name }}</td>
                        <td>{{ session.started_at.strftime('%Y-%m-%d %H:%M:%S') if session.started_at else 'N/A' }}</td>
                        <td>
                            {% if session.started_at and session.completed_at %}
                            {{ ((session.completed_at - session.started_at).total_seconds()) | round(2) }}s
                            {% else %}
                            N/A
                            {% endif %}
                        </td>
                        <td>{{ session.jobs_found }}</td>
                        <td>{{ session.jobs_new }}</td>
                        <td>{{ session.jobs_updated }}</td>
                        <td>{{ session.jobs_removed }}</td>
                        <td>
                            <span class="badge {{ 'active' if session.status == 'completed' else 'inactive' }}">
                                {{ session.status }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }

        function filterJobs() {
            const companyFilter = document.getElementById('company-filter').value.toLowerCase();
            const roleFilter = document.getElementById('role-filter').value.toLowerCase();
            const sourceFilter = document.getElementById('source-filter').value.toLowerCase();
            const searchFilter = document.getElementById('search-filter').value.toLowerCase();

            const rows = document.querySelectorAll('#jobs-tbody tr');

            rows.forEach(row => {
                const company = row.dataset.company.toLowerCase();
                const role = (row.dataset.role || '').toLowerCase();
                const source = (row.dataset.source || '').toLowerCase();
                const title = row.dataset.title.toLowerCase();

                const matchCompany = !companyFilter || company === companyFilter;
                const matchRole = !roleFilter || role === roleFilter;
                const matchSource = !sourceFilter ||
                    (sourceFilter === 'linkedin_aggregator' && source === 'linkedin_aggregator') ||
                    (sourceFilter === 'company' && source !== 'linkedin_aggregator' && source !== '');
                const matchSearch = !searchFilter || title.includes(searchFilter);

                if (matchCompany && matchRole && matchSource && matchSearch) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

# Role categories for filtering
ROLE_PATTERNS = {
    'Software Engineer': ['software engineer', 'software developer', 'backend engineer', 'frontend engineer',
                          'fullstack engineer', 'full-stack engineer', 'full stack engineer', 'backend developer',
                          'frontend developer', 'fullstack developer', 'full-stack developer'],
    'Hardware Engineer': ['hardware engineer', 'hardware developer', 'fpga engineer', 'asic engineer',
                          'chip designer', 'vlsi engineer', 'embedded engineer', 'embedded developer',
                          'firmware engineer', 'firmware developer', 'pcb engineer', 'electrical engineer',
                          'electronics engineer', 'rf engineer', 'analog engineer', 'digital design engineer'],
    'DevOps/SRE': ['devops', 'sre', 'site reliability', 'platform engineer', 'infrastructure engineer',
                   'cloud engineer', 'systems engineer'],
    'Data Engineer': ['data engineer', 'data platform', 'etl developer', 'analytics engineer'],
    'Data Scientist': ['data scientist', 'machine learning', 'ml engineer', 'ai engineer', 'research scientist',
                       'deep learning', 'nlp engineer'],
    'Product Manager': ['product manager', 'product owner', 'pm ', 'group product manager'],
    'Engineering Manager': ['engineering manager', 'r&d manager', 'team lead', 'tech lead', 'vp r&d',
                            'vp engineering', 'director of engineering', 'head of engineering', 'cto'],
    'QA/Testing': ['qa engineer', 'quality assurance', 'test engineer', 'sdet', 'automation engineer',
                   'quality engineer'],
    'Security': ['security engineer', 'security analyst', 'appsec', 'infosec', 'penetration', 'security researcher'],
    'Designer': ['designer', 'ux', 'ui ', 'product designer', 'graphic designer'],
    'Sales/BD': ['sales', 'business development', 'account executive', 'account manager', 'bdr', 'sdr'],
    'Marketing': ['marketing', 'growth', 'content', 'brand', 'communications'],
    'HR/Recruiting': ['recruiter', 'talent acquisition', 'hr ', 'human resources', 'people operations'],
    'Finance': ['finance', 'accountant', 'controller', 'fp&a', 'financial analyst'],
    'Support': ['support engineer', 'customer success', 'technical support', 'customer support'],
    'Operations': ['operations', 'office manager', 'admin', 'procurement'],
}

def extract_role(title: str) -> str:
    """Extract role category from job title."""
    title_lower = title.lower()
    for role, patterns in ROLE_PATTERNS.items():
        for pattern in patterns:
            if pattern in title_lower:
                return role
    return 'Other'


@app.route('/')
def index():
    with db.get_session() as session:
        # Get statistics
        total_jobs = session.query(func.count(JobPosition.id)).scalar()
        active_jobs = session.query(func.count(JobPosition.id)).filter(JobPosition.is_active == True).scalar()
        total_companies = session.query(func.count(Company.id)).scalar()
        active_companies = session.query(func.count(Company.id)).filter(Company.is_active == True).scalar()
        
        last_session = session.query(ScrapingSession).order_by(desc(ScrapingSession.started_at)).first()
        last_scrape = last_session.started_at.strftime('%Y-%m-%d %H:%M') if last_session and last_session.started_at else 'Never'
        
        stats = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_companies': total_companies,
            'active_companies': active_companies,
            'last_scrape': last_scrape
        }
        
        # Get all companies
        companies = session.query(Company).order_by(Company.name).all()
        
        # Get companies with job counts
        companies_with_stats = session.query(
            Company,
            func.count(JobPosition.id).label('job_count')
        ).outerjoin(JobPosition).group_by(Company.id).order_by(desc('job_count')).all()
        
        companies_with_stats = [
            {
                'name': c.name,
                'website': c.website,
                'industry': c.industry,
                'location': c.location,
                'job_count': count,
                'last_scraped_at': c.last_scraped_at,
                'is_active': c.is_active
            }
            for c, count in companies_with_stats
        ]
        
        # Get all active jobs (ordered by posted date)
        jobs = session.query(JobPosition).join(Company).filter(JobPosition.is_active == True).order_by(desc(JobPosition.posted_date)).all()
        jobs_data = [
            {
                'company_name': job.company.name,
                'title': job.title,
                'location': job.location,
                'remote_type': job.remote_type,
                'source_type': job.source_type,
                'role': extract_role(job.title),
                'department': job.department,
                'posted_date': job.posted_date,
                'job_url': job.job_url,
                'is_active': job.is_active
            }
            for job in jobs
        ]

        # Get unique roles for the filter dropdown
        roles = sorted(set(job['role'] for job in jobs_data))
        
        # Get recent scraping sessions
        sessions = session.query(ScrapingSession).join(Company).order_by(desc(ScrapingSession.started_at)).limit(50).all()
        sessions_data = [
            {
                'company_name': s.company.name,
                'started_at': s.started_at,
                'completed_at': s.completed_at,
                'jobs_found': s.jobs_found,
                'jobs_new': s.jobs_new,
                'jobs_updated': s.jobs_updated,
                'jobs_removed': s.jobs_removed,
                'status': s.status
            }
            for s in sessions
        ]
        
        return render_template_string(
            HTML_TEMPLATE,
            stats=stats,
            companies=companies,
            companies_with_stats=companies_with_stats,
            jobs=jobs_data,
            roles=roles,
            sessions=sessions_data
        )

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Starting Database Viewer")
    print("=" * 80)
    print("📊 Open your browser at: http://localhost:5001")
    print("=" * 80)
    app.run(host='0.0.0.0', port=5001, debug=True)

