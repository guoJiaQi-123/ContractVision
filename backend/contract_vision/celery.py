import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contract_vision.settings.development')

app = Celery('contract_vision')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
