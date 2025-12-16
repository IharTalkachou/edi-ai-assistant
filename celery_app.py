# конфигурация менеджера задач redis
from celery import Celery
import os

# адрес redis: если локально - localhost, если внутри докера - имя сервиса redis
# здесь запускаю воркера вручную, поэтому localhost
REDIS_URL = 'redis://localhost:6379/0'

# инстанс менеджера задач
celery_app = Celery(
    'edi_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# настройки
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True
)