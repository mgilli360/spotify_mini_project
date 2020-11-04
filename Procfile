web: gunicorn spotapp:app --workers=3 --threads=3
worker: celery worker --spotapp:celery --loglevel=info