import datetime
import time
import requests
import os, sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.job import Job  
from shared.models.scrape_target import ScrapeTarget

# Configure logging to include timestamps, log level, and message.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
        logging.info("Scheduled job '%s' for %s", task_name, scheduled_date)
    except SQLAlchemyError as e:
        db_session.rollback()
        logging.error("Error adding job '%s': %s", task_name, e)
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
    Every 30 minutes, check the job_scheduler table for pending jobs whose scheduled date is now (or in the past).
    For each job, this function determines the corresponding API endpoint based on the task name and appends
    the job id as a path parameter. It then sends an HTTP GET request to the endpoint. On success, the job's status
    is updated to indicate completion; on failure, an error message is recorded.
    """
    now = datetime.datetime.now()
    db_session = SessionLocal()
    try:
        # Query for pending jobs whose scheduled_date is now or has passed.
        pending_jobs = db_session.query(Job).filter(
            Job.status == 0,
            Job.scheduled_date <= now
        ).all()

        logging.info("Found %d pending jobs to initiate.", len(pending_jobs))
        
        for job in pending_jobs:
            task_lower = job.task_name.lower()
            url_to_call = None
            
            logging.info("Starting '%s' (ID: %d)", job.task_name, job.id)
            
            # Mark job as in-progress.
            job.status = 1
            job.updated_at = datetime.datetime.now().date()
            db_session.commit()
            logging.info("Successfully initiated '%s' (ID: %d)", job.task_name, job.id)
            time.sleep(2)

            
            # Determine the URL based on task name and append job id as a path parameter.
            if "web scrape" in task_lower:
                url_to_call = f"https://scraper.bluedune-c06522b4.uaenorth.azurecontainerapps.io/website_scrape/{job.id}"
            elif "insta scrape" in task_lower:
                url_to_call = f"https://scraper.bluedune-c06522b4.uaenorth.azurecontainerapps.io/instagram_scrape/{job.id}"
            elif "create media" in task_lower:
                url_to_call = f"http://localhost:3002/generate-image/{job.id}"
            elif "post image" in task_lower:
                if "whatsapp" in task_lower:
                    url_to_call = f"http://localhost:3000/post-image/{job.id}"
                else:
                    url_to_call = f"http://localhost:3003/post-image/{job.id}"
            else:
                logging.info("No matching endpoint for task: %s", job.task_name)
                continue

            # Send an HTTP GET request to the selected endpoint.
            try:
                response = requests.get(url_to_call)

                if response.status_code != 200:
                    job.status = -1
                    job.error_message = f"HTTP {response.status_code}"
                    logging.error("Failed to initiate '%s' (ID: %d). HTTP %d", job.task_name, job.id, response.status_code, response.json())
            except Exception as e:
                job.status = -1
                job.error_message = str(e)
                logging.error("Exception while initiating '%s' (ID: %d): %s", job.task_name, job.id, e)
            
            job.updated_at = datetime.datetime.now()
            db_session.commit()

    except SQLAlchemyError as e:
        db_session.rollback()
        logging.error("Database error in initiate_tasks: %s", e)
    finally:
        db_session.close()


if __name__ == "__main__":

    scheduler = BackgroundScheduler()
    # Schedule the weekly job to run every Sunday at midnight (00:00 UTC).
    # scheduler.add_job(create_weekly_instagram_jobs, 'cron', day_of_week='sun', hour=0, minute=0)
    # scheduler.add_job(create_weekly_scrape_jobs, 'cron', day_of_week='sun', hour=0, minute=0)
    scheduler.add_job(initiate_tasks, 'interval', minutes=0.5)
    
    # Optionally, run tasks immediately at startup for testing:
    # create_weekly_instagram_jobs()
    # create_weekly_scrape_jobs()
    # initiate_tasks()

    scheduler.start()
    logging.info("Scheduler started...")
    
    try:
        # Keep the main thread alive.
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down scheduler...")
        scheduler.shutdown()
