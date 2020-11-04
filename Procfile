web: gunicorn spotapp:app --workers=3 --threads=3
worker: celery worker --app=spotapp:celery --loglevel=info