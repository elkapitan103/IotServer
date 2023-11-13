from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
from discovery import get_discovered_data
import logging
import atexit

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def sample_job():
    try:
        data = get_discovered_data()
        logger.info(f"Sample job executed at {datetime.datetime.now()}")
    except Exception as e:
        logger.error(f"Error during sample job execution: {e}")

job = scheduler.add_job(sample_job, trigger=IntervalTrigger(seconds=10), id='sample_job', replace_existing=True)

scheduler.start()

# Ensure the scheduler shuts down gracefully when the application exits
atexit.register(lambda: scheduler.shutdown())

