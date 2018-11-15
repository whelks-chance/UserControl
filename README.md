# UserControl

Django app, python 3.5.2

Copy into place, run 

    pip install -r requirements.txt

    python manage.py migrate
    
    python manage.py runserver
    
Two endpoints:

/generate_new_user and /disable_expired_users

UserControl/tests.py runs both with http GET to check successful creation and removal of users.
