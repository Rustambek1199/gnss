import multiprocessing
import os

port = os.environ.get('PORT', '5000')
bind = os.environ.get('GUNICORN_BIND', f'0.0.0.0:{port}')
workers = int(os.environ.get('GUNICORN_WORKERS', 2))
threads = int(os.environ.get('GUNICORN_THREADS', 4))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
keepalive = 5

accesslog = '-'
errorlog = '-'
loglevel = 'info'
