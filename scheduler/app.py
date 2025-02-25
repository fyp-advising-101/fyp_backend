import datetime
import time
import requests
import os, sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database import engine, SessionLocal
from shared.models.base import Base

from shared.models.job import Job  
from shared.models.scrape_target import ScrapeTarget
Base.metadata.create_all(bind=engine)

scraping_url = ""
media_gen_url = ""
instagram_url = ""
whatsapp_url = ""

def add_job(task_name: str, scheduled_date: datetime.datetime):
    """
    Creates a new job entry in the job_scheduler table.
    
    :param task_name: Name of the job.
    :param scheduled_date: The datetime when the job should run.
    """
    db_session = SessionLocal()
    now = datetime.datetime.now()
    try:
        new_job = Job(
            task_name=task_name,
            scheduled_date=scheduled_date,
            status=0,         # initial status set to pending
            error_message=None,
            created_at=now,
            updated_at=now
        )
        db_session.add(new_job)
        db_session.commit()
        print(f"[{datetime.datetime.now()}] Scheduled job '{task_name}' for {scheduled_date}")
    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"[{datetime.datetime.now()}] Error adding job '{task_name}': {e}")
    finally:
        db_session.close()

def get_next_monday(today: datetime.date) -> datetime.date:
    """
    Given today's date, compute the date of next Monday.
    If today is Monday, then next Monday is 7 days away.
    """
    weekday = today.weekday()  # Monday=0, Sunday=6
    days_ahead = 7 - weekday if weekday != 0 else 7
    return today + datetime.timedelta(days=days_ahead)

def initiate_tasks():
    """
    Every 30 minutes, check the job_scheduler table for jobs that are pending and
    whose scheduled date is now (or in the past). For each such job, send an HTTP
    request to the corresponding API endpoint based on the job's task name.
    If the API call is successful, update the job's status to 'completed'; otherwise,
    record an error message.
    """
    now = datetime.datetime.now()
    db_session = SessionLocal()
    try:
        # Query for pending jobs whose scheduled_date is now or has passed.
        pending_jobs = db_session.query(Job).filter(
            Job.status == 0,
            Job.scheduled_date <= now
        ).all()
        
        print(f"[{datetime.datetime.now()}] Found {len(pending_jobs)} pending jobs to initiate.")
        
        for job in pending_jobs:
            # Determine the URL based on the task name.
            task_lower = job.task_name.lower()
            url_to_call = None
            if "web scrape" in task_lower:
                url_to_call = scraping_url + "endpoint and job id"
            elif "insta scrape" in task_lower:
                url_to_call = scraping_url + "endpoint and job id"
            elif "create media" in task_lower:
                url_to_call = scraping_url + "endpoint and job id" 
            elif "post image" in task_lower:
                url_to_call = instagram_url
                url_to_call = whatsapp_url
            else:
                print(f"[{datetime.datetime.now()}] No matching endpoint for task: {job.task_name}")
                continue
            
            # Send an HTTP GET request to the endpoint.
            try:
                response = requests.get(url_to_call)
                # Here we assume a status code of 200 indicates success.
                if response.status_code == 200:
                    job.status = 1
                    print(f"[{datetime.datetime.now()}] Successfully initiated '{job.task_name}' (ID: {job.id})")
                else:
                    job.status = -1
                    job.error_message = f"HTTP {response.status_code}"
                    print(f"[{datetime.datetime.now()}] Failed to initiate '{job.task_name}' (ID: {job.id}). HTTP {response.status_code}")
            except Exception as e:
                job.status = -1
                job.error_message = str(e)
                print(f"[{datetime.datetime.now()}] Exception while initiating '{job.task_name}' (ID: {job.id}): {e}")
            
            # Update the updated_at field.
            job.updated_at = datetime.datetime.now()
            # Commit after each job update (or commit once after processing all jobs).
            db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"[{datetime.datetime.now()}] Database error in initiate_tasks: {e}")
    finally:
        db_session.close()

def create_weekly_instagram_jobs():
    """
    Creates two sets of jobs for the upcoming week:
      - For each weekday (Monday-Friday), create a "post on instagram" job at 10 AM.
      - For each weekday (Monday-Friday), create a "create instagram post" job
        scheduled the day before at 2 AM.
    This function is intended to be run weekly (for example, every Sunday at midnight)
    so that the next week's jobs are created in advance.
    """
    today = datetime.datetime.now().date()
    next_monday = get_next_monday(today)
    
    print(f"[{datetime.datetime.now()}] Creating weekly Instagram jobs for week starting on {next_monday}")
    
    # Iterate Monday (0) through Friday (4)
    for day_offset in range(5):
        # Compute the weekday date for "post on instagram"
        post_date = next_monday + datetime.timedelta(days=day_offset)
        # Set the scheduled time for posting at 10 AM (UTC, adjust if needed)
        post_datetime = datetime.datetime.combine(post_date, datetime.time(hour=10, minute=0))
        add_job(task_name="post on instagram", scheduled_date=post_datetime)
        
        # For "create instagram post", schedule it the day before at 2 AM.
        # For Monday, this will be the previous Sunday.
        create_date = post_date - datetime.timedelta(days=1)
        create_datetime = datetime.datetime.combine(create_date, datetime.time(hour=2, minute=0))
        add_job(task_name="create instagram post", scheduled_date=create_datetime)

def create_weekly_scrape_jobs():
    """
    For each scrape target in the ScrapeTarget table, create a series of scheduled
    jobs for the upcoming week based on the target's frequency (in hours).
    
    The week is defined as starting on the next Monday at 00:00 UTC and ending 7 days later.
    """
    today = datetime.datetime.now().date()
    week_start_date = get_next_monday(today)
    week_start_dt = datetime.datetime.combine(week_start_date, datetime.time(0, 0))
    week_end_dt = week_start_dt + datetime.timedelta(days=7)
    
    print(f"[{datetime.datetime.now()}] Creating weekly scrape jobs for targets between {week_start_dt} and {week_end_dt}")

    # Retrieve all scrape targets.
    db_session = SessionLocal()
    try:
        scrape_targets = db_session.query(ScrapeTarget).all()
    except SQLAlchemyError as e:
        print(f"Error retrieving scrape targets: {e}")
        db_session.rollback()
        return
    finally:
        db_session.close()
    
    # For each scrape target, schedule jobs at the specified frequency.
    for target in scrape_targets:
        frequency_hours = target.frequency
        # Start scheduling at the beginning of the week.
        next_run = week_start_dt
        
        # Continue creating jobs until the scheduled time reaches the end of the week.
        while next_run < week_end_dt:
            # Compose a descriptive task name.
            task_name = (f"scrape {target.type}")
            add_job(task_name=task_name, scheduled_date=next_run)
            # Increment the next run time by the frequency (in hours).
            next_run += datetime.timedelta(hours=frequency_hours)

if __name__ == "__main__":

    scheduler = BackgroundScheduler()
    # Schedule the weekly job to run every Sunday at midnight (00:00 UTC).
    #scheduler.add_job(create_weekly_instagram_jobs, 'cron', day_of_week='sun', hour=0, minute=0)
    #scheduler.add_job(create_weekly_scrape_jobs, 'cron', day_of_week='sun', hour=0, minute=0)
    scheduler.add_job(initiate_tasks, 'interval', minutes=0.5)
    
    # Optionally, you could run the weekly job immediately at startup for testing:
    # create_weekly_instagram_jobs()
    # create_weekly_scrape_jobs()
    # initiate_tasks()

    scheduler.start()
    print(f"[{datetime.datetime.now()}] Scheduler started...")
    
    try:
        # Keep the main thread alive.
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down scheduler...")
        scheduler.shutdown()
