pip3 install -r requirements.txt
python manage.py makemigrations
python manage.py migrate 
cat initial_config.py | python manage.py shell