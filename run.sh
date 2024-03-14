sudo gunicorn3 storemanager.wsgi:application --name storemanager --workers 3 --bind=0.0.0.0:8080 --daemon

sudo systenctl restart nginx