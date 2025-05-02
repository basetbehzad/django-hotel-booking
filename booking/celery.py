from celery.schedules import crontab
from celery import Celery
import os
import multiprocessing

multiprocessing.set_start_method("spawn", force=True)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking.settings')
celery_app = Celery('booking')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

celery_app.autodiscover_tasks()

# Periodic Task (Run Every Minute)
celery_app.conf.beat_schedule = {
    'auto_cancel_unpaid_bookings': {
        'task': 'reservation.tasks.auto_cancel_unpaid_bookings',
        'schedule': crontab(minute='*/1'),  # Every 1 minute
    },
}
