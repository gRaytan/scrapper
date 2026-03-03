#!/usr/bin/env python3
"""Preview script for alert creation reminder email template."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Jinja2 environment
TEMPLATES_DIR = project_root / "src" / "templates" / "emails"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

# Sample job data
sample_jobs = [
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Senior Full Stack Engineer",
        "company_name": "Microsoft",
        "location": "Tel Aviv, Israel",
        "posted_date": "2 days ago",
        "remote_type": "Hybrid"
    },
    {
        "id": "223e4567-e89b-12d3-a456-426614174001",
        "title": "Backend Developer - Python",
        "company_name": "Google",
        "location": "Haifa, Israel",
        "posted_date": "1 day ago",
        "remote_type": "Remote"
    },
    {
        "id": "323e4567-e89b-12d3-a456-426614174002",
        "title": "DevOps Engineer",
        "company_name": "Amazon",
        "location": "Jerusalem, Israel",
        "posted_date": "3 days ago",
        "remote_type": "On-site"
    },
    {
        "id": "423e4567-e89b-12d3-a456-426614174003",
        "title": "Software Engineer",
        "company_name": "Apple",
        "location": "Herzliya, Israel",
        "posted_date": "5 days ago",
        "remote_type": "Hybrid"
    },
    {
        "id": "523e4567-e89b-12d3-a456-426614174004",
        "title": "Full Stack Developer",
        "company_name": "Meta",
        "location": "Tel Aviv, Israel",
        "posted_date": "1 week ago",
        "remote_type": "Remote"
    }
]

def preview_html():
    """Generate and save HTML preview."""
    template = jinja_env.get_template("alert_creation_reminder.html")
    
    context = {
        "user_name": "Gil",
        "reminder_number": 1,
        "jobs": sample_jobs,
        "job_count": len(sample_jobs),
        "base_url": "https://hiddenjobs.me",
        "current_year": datetime.now().year
    }
    
    html_content = template.render(context)
    
    # Save to file
    output_file = project_root / "alert_reminder_preview.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTML preview saved to: {output_file}")
    print(f"📂 Open in browser: file://{output_file.absolute()}")
    return output_file

def preview_text():
    """Generate and save text preview."""
    template = jinja_env.get_template("alert_creation_reminder.txt")
    
    context = {
        "user_name": "Gil",
        "reminder_number": 1,
        "jobs": sample_jobs,
        "job_count": len(sample_jobs),
        "base_url": "https://hiddenjobs.me",
        "current_year": datetime.now().year
    }
    
    text_content = template.render(context)
    
    # Save to file
    output_file = project_root / "alert_reminder_preview.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text_content)
    
    print(f"✅ Text preview saved to: {output_file}")
    print("\n" + "="*80)
    print("TEXT VERSION:")
    print("="*80)
    print(text_content)
    print("="*80)
    return output_file

if __name__ == "__main__":
    print("🎨 Generating Alert Creation Reminder Email Preview...\n")
    
    try:
        html_file = preview_html()
        print()
        text_file = preview_text()
        
        print(f"\n✨ Preview complete!")
        print(f"\n💡 To view the HTML email:")
        print(f"   open {html_file.absolute()}")
        
    except Exception as e:
        print(f"❌ Error generating preview: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

