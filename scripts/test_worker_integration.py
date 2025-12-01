#!/usr/bin/env python3
"""
Test worker integration with orchestrator.
Tests scraping a single company through the Celery worker system.
"""
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workers.celery_app import celery_app
from src.workers.tasks import scrape_single_company
from celery.result import AsyncResult


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"✗ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")


def check_worker_status():
    """Check if Celery workers are running."""
    print_header("Checking Worker Status")
    
    try:
        # Inspect active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print_success(f"Found {len(active_workers)} active worker(s)")
            for worker_name, tasks in active_workers.items():
                print(f"  • {worker_name}: {len(tasks)} active task(s)")
            return True
        else:
            print_error("No active workers found")
            print_info("Please start workers with: ./scripts/setup_workers.sh start")
            return False
    except Exception as e:
        print_error(f"Failed to connect to workers: {e}")
        print_info("Make sure Redis and Celery workers are running")
        return False


def check_registered_tasks():
    """Check registered tasks."""
    print_header("Checking Registered Tasks")
    
    try:
        inspect = celery_app.control.inspect()
        registered = inspect.registered()
        
        if registered:
            for worker_name, tasks in registered.items():
                print_success(f"Worker: {worker_name}")
                for task in sorted(tasks):
                    if 'src.workers.tasks' in task:
                        print(f"  • {task}")
            return True
        else:
            print_error("No registered tasks found")
            return False
    except Exception as e:
        print_error(f"Failed to get registered tasks: {e}")
        return False


def test_sync_execution(company_name):
    """Test synchronous task execution (wait for result)."""
    print_header(f"Test 1: Synchronous Execution - {company_name}")
    
    print_info(f"Triggering scrape for {company_name} (synchronous)...")
    print_info("This will wait for the task to complete...")
    
    try:
        # Call task synchronously (wait for result)
        result = scrape_single_company.apply_async(
            args=[company_name, False],
            kwargs={}
        )
        
        print_success(f"Task queued with ID: {result.id}")
        print_info("Waiting for task to complete (timeout: 300 seconds)...")
        
        # Wait for result with timeout
        task_result = result.get(timeout=300)
        
        print_success("Task completed successfully!")
        print("\nResults:")
        print(f"  • Company: {task_result.get('company_name')}")
        print(f"  • Status: {task_result.get('status')}")
        print(f"  • Jobs Found: {task_result.get('jobs_found', 0)}")
        print(f"  • Jobs New: {task_result.get('jobs_new', 0)}")
        print(f"  • Jobs Updated: {task_result.get('jobs_updated', 0)}")
        print(f"  • Jobs Removed: {task_result.get('jobs_removed', 0)}")
        print(f"  • Duration: {task_result.get('duration_seconds', 0):.2f} seconds")
        
        if task_result.get('error'):
            print_error(f"Error: {task_result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Task failed: {e}")
        return False


def test_async_execution(company_name):
    """Test asynchronous task execution (queue and check status)."""
    print_header(f"Test 2: Asynchronous Execution - {company_name}")
    
    print_info(f"Triggering scrape for {company_name} (asynchronous)...")
    print_info("This will queue the task and return immediately...")
    
    try:
        # Call task asynchronously (don't wait)
        result = scrape_single_company.delay(company_name, False)
        
        print_success(f"Task queued with ID: {result.id}")
        print_info("Task is running in the background...")
        
        # Poll for status
        max_wait = 300  # 5 minutes
        poll_interval = 2  # 2 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            status = result.status
            print(f"  Status: {status} (elapsed: {elapsed}s)", end='\r')
            
            if status == 'SUCCESS':
                print()  # New line
                task_result = result.result
                print_success("Task completed successfully!")
                print("\nResults:")
                print(f"  • Company: {task_result.get('company_name')}")
                print(f"  • Jobs Found: {task_result.get('jobs_found', 0)}")
                print(f"  • Jobs New: {task_result.get('jobs_new', 0)}")
                print(f"  • Jobs Updated: {task_result.get('jobs_updated', 0)}")
                return True
            elif status == 'FAILURE':
                print()  # New line
                print_error(f"Task failed: {result.result}")
                return False
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        print()  # New line
        print_error("Task timed out")
        return False
        
    except Exception as e:
        print_error(f"Task failed: {e}")
        return False


def check_task_result(task_id):
    """Check the result of a specific task."""
    print_header(f"Checking Task Result: {task_id}")
    
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        print(f"Task ID: {result.id}")
        print(f"Status: {result.status}")
        
        if result.ready():
            if result.successful():
                print_success("Task completed successfully")
                print("\nResult:")
                print(result.result)
            else:
                print_error("Task failed")
                print(f"Error: {result.result}")
        else:
            print_info("Task is still running or pending")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to get task result: {e}")
        return False


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test worker integration')
    parser.add_argument('--company', type=str, default='Monday.com',
                        help='Company name to test (default: Monday.com)')
    parser.add_argument('--mode', type=str, choices=['sync', 'async', 'both', 'status'],
                        default='both', help='Test mode (default: both)')
    parser.add_argument('--task-id', type=str, help='Check status of specific task ID')
    
    args = parser.parse_args()
    
    print_header("Worker Integration Test")
    print(f"Company: {args.company}")
    print(f"Mode: {args.mode}")
    
    # Check if task ID provided
    if args.task_id:
        check_task_result(args.task_id)
        return
    
    # Check worker status
    if not check_worker_status():
        print_error("\nWorkers are not running. Please start them first:")
        print_info("  ./scripts/setup_workers.sh start")
        sys.exit(1)
    
    # Check registered tasks
    if not check_registered_tasks():
        print_error("\nNo tasks registered. Check worker configuration.")
        sys.exit(1)
    
    # Run tests based on mode
    success = True
    
    if args.mode in ['sync', 'both']:
        if not test_sync_execution(args.company):
            success = False
    
    if args.mode in ['async', 'both']:
        if not test_async_execution(args.company):
            success = False
    
    if args.mode == 'status':
        check_worker_status()
        check_registered_tasks()
    
    # Summary
    print_header("Test Summary")
    if success:
        print_success("All tests passed!")
        print_info("\nNext steps:")
        print("  1. Check database: .venv/bin/python scripts/query_db.py jobs")
        print("  2. View logs: ./scripts/setup_workers.sh logs")
        print("  3. Monitor workers: ./scripts/setup_workers.sh status")
    else:
        print_error("Some tests failed")
        print_info("Check logs: ./scripts/setup_workers.sh logs")
        sys.exit(1)


if __name__ == '__main__':
    main()

