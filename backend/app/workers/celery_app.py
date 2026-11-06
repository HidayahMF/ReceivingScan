from celery import Celery
from ..config import get_settings

celery_app = Celery("receiving_ai", broker=get_settings().redis_url, backend=get_settings().redis_url)
