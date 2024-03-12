# Inventory management system

Installation guide

- create .env file
```shell
# SQL Configurations
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=DB
SQL_USER=USERNAME
SQL_PASSWORD=PASSWORD
SQL_HOST=localhost


ADMIN_USERNAME = "username"
ADMIN_EMAIL = "email@address.domain"
ADMIN_PASSWORD = "password"
```

- run
    ```shell
    sh entrypoint.sh
    sh run.sh
    ```