web: gunicorn mysite2.wsgi -c gunicorn.conf.py
release: python manage.py migrate --noinput && python manage.py import_site_views
