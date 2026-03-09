from celery import Celery
from services.config import configs as config
from celery.schedules import crontab

REDIS_URL = config.REDIS_URI if "redis" in config.REDIS_URI else "redis://localhost:6379/0"

app = Celery("donation_app")

app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='msgpack',
    result_serializer='msgpack',
    accept_content=['msgpack', 'pickle', 'json'],
    worker_prefetch_multiplier=1,      
    task_acks_late=True,              
    task_reject_on_worker_lost=True,
    redis_max_connections=512,        
    broker_pool_limit=None,            
    redis_socket_keepalive=True,
    redis_socket_connect_timeout=10,
    result_persistent=False,          
    task_ignore_result=False,
    task_always_eager=False,          
    result_expires=600,                
    enable_utc=True,
    timezone='Asia/Jakarta',
    broker_connection_retry_on_startup=True
)
