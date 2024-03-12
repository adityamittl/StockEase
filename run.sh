export IP = "" #IP to bind to
gunicorn --bind ${IP} storemanager.wsgi