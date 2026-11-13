import os
from app import create_app

# Ishlab chiqarish muhiti (Gunicorn, uWSGI, Waitress uchun)
env = os.environ.get('FLASK_ENV', 'production')
application = create_app(env)

if __name__ == '__main__':
    application.run()
