#!/usr/bin/env python3
"""
Test script for OneSignal email service.

Usage:
    python scripts/test_onesignal_email.py <email_address>
    
Example:
    python scripts/test_onesignal_email.py gil@example.com
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.onesignal_email_service import onesignal_email_service


def test_simple_email(to_email: str):
    """Send a simple test email."""
    print(f"\n{'='*60}")
    print("Testing OneSignal Email Service")
    print(f"{'='*60}")
    
    print(f"\nConfiguration:")
    print(f"  is_configured: {onesignal_email_service.is_configured}")
    print(f"  from_email: {onesignal_email_service.from_email}")
    print(f"  from_name: {onesignal_email_service.from_name}")
    print(f"  app_id: {onesignal_email_service.app_id[:8]}..." if onesignal_email_service.app_id else "  app_id: Not set")
    
    if not onesignal_email_service.is_configured:
        print("\n❌ OneSignal not configured! Set ONESIGNAL_APP_ID and ONESIGNAL_API_KEY")
        return False
    
    print(f"\nSending test email to: {to_email}")
    
    # Test 1: Simple email
    print("\n--- Test 1: Simple Email ---")
    result = onesignal_email_service.send_email(
        to_email=to_email,
        subject="🧪 HiddenJobs Test Email",
        html_content="""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #6366f1;">Test Email from HiddenJobs</h1>
            <p>This is a test email sent via <strong>OneSignal</strong>.</p>
            <p>If you received this, the integration is working! 🎉</p>
            <hr>
            <p style="color: #666; font-size: 12px;">Sent from HiddenJobs test script</p>
        </body>
        </html>
        """
    )
    
    if result.get('success'):
        print(f"  ✅ Simple email sent! Message ID: {result.get('id')}")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
        return False
    
    # Test 2: Job digest email
    print("\n--- Test 2: Job Digest Email ---")
    test_jobs = [
        {
            'title': 'Senior Software Engineer',
            'company_name': 'TechCorp',
            'location': 'Tel Aviv, Israel',
            'job_url': 'https://hiddenjobs.me/position/test-1',
            'posted_date': 'Feb 24'
        },
        {
            'title': 'Product Manager',
            'company_name': 'StartupXYZ',
            'location': 'Remote',
            'job_url': 'https://hiddenjobs.me/position/test-2',
            'posted_date': 'Feb 23'
        },
        {
            'title': 'DevOps Engineer',
            'company_name': 'CloudInc',
            'location': 'Herzliya, Israel',
            'job_url': 'https://hiddenjobs.me/position/test-3',
            'posted_date': 'Feb 22'
        }
    ]
    
    result = onesignal_email_service.send_job_digest_email(
        to_email=to_email,
        user_name="Test User",
        jobs=test_jobs,
        alert_name="Test Alert"
    )
    
    if result.get('success'):
        print(f"  ✅ Job digest email sent! Message ID: {result.get('id')}")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
        return False
    
    print(f"\n{'='*60}")
    print("✅ All tests passed!")
    print(f"{'='*60}\n")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_onesignal_email.py <email_address>")
        print("Example: python scripts/test_onesignal_email.py gil@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    success = test_simple_email(email)
    sys.exit(0 if success else 1)
