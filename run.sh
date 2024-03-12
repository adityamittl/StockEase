EXPORT IP_ADD = "140.238.166.248" #IP to bind to
gunicorn --bind ${IP_ADD} storemanager.wsgi