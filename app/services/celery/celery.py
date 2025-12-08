from celery import Celery
from celery.schedules import crontab

celery_app = Celery('app', broker='amqp://rabbitmq:rabbitmq@rabbitmq:5672')

celery_app.autodiscover_tasks(['services.celery.tasks'])


celery_app.conf.beat_schedule = {
    'make-analysis-every-week': {
        'task': 'services.celery.tasks.get_analysis',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),
    },
}
