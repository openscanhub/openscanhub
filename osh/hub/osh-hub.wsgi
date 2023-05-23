import os

from django.core.wsgi import get_wsgi_application

# tweak PYTHONPATH if needed (usually if project is deployed outside site-packages)
# sys.path.append("/var/www/django")


os.environ['DJANGO_SETTINGS_MODULE'] = 'osh.hub.settings'
application = get_wsgi_application()
