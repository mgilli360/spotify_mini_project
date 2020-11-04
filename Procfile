web: gunicorn spotapp:app --workers=3 --threads=3
worker: celery --app spotapp.celery worker --pool=gevent --loglevel=INFO