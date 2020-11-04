web: gunicorn spotapp:app --workers=1 --threads=1
worker: celery --app spotapp.celery worker --pool=gevent --loglevel=INFO