pip3 install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate 
cat initial_config.py | python3 manage.py shell