import json

import datetime
from django.http import HttpResponse
from django.shortcuts import render
import uuid
import subprocess
import sys
import crypt

# Create your views here.
from usercontroller import models


def remove_openssh_user(db_user):
    assert isinstance(db_user, models.User)
    username = db_user.username
    ssh = subprocess.Popen(["sudo",
                           "/home/usercontroller/addsftpuser.sh",
                           username],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print(sys.stderr, "ERROR: {}".format(error))
        return False
    else:
        print(result)
        return True


def create_openssh_user(username, password):
    print(username, 'length {}'.format(len(username)))
    crypted_password = crypt.crypt(password)
    print(password, crypted_password)

    ssh = subprocess.Popen(["sudo",
                           "/home/usercontroller/addsftpuser.sh",
                           username,
                           crypted_password],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print(sys.stderr, "ERROR: {}".format(error))
        return False
    else:
        print(result)
        return True


def disable_user(db_user):
    assert isinstance(db_user, models.User)
    db_user.disabled = True
    db_user.save()


def check_users(request):
    active_users = []
    disabled_users = []
    users_disabled = []
    errors = []

    print(60 * 60 * 24)
    for u in models.User.objects.all():
        if not u.disabled:
            print(datetime.datetime.now(tz=datetime.timezone.utc))
            print(u.created)
            time_diff = datetime.datetime.now(tz=datetime.timezone.utc) - u.created

            print('\n', time_diff, type(time_diff))
            print(time_diff.total_seconds())
            print(time_diff.total_seconds() > 60 * 60 * 24)

            if time_diff.total_seconds() > 60 * 60 * 24:
                success = remove_openssh_user(u)

                if success:
                    disable_user(u)
                    users_disabled.append(u.username)
                else:
                    errors.append(u.username)
            else:
                active_users.append(u.username)
        else:
            disabled_users.append(u.username)

    api_data = {
        'active_users': active_users,
        'disabled_users': disabled_users,
        'users_disabled': users_disabled,
        'errors': errors
    }
    return HttpResponse(json.dumps(api_data, indent=4), content_type="application/json")


def generate_new_user(request):
    errors = []

    # Apparently we have a 32 char username limit, so trim what we have
    username = 'u{}'.format(
        ''.join(str(uuid.uuid4())[:31])
    )
    password = uuid.uuid4()

    if username and password:
        success = create_openssh_user(username, str(password))
        if success:
            new_user = models.User(username=username)
            print(new_user)
            new_user.save()
        else:
            errors.append('Failed to create user {}'.format(username))

    api_data = {
        'username': str(username),
        'password': str(password),
        'errors': errors
    }
    return HttpResponse(json.dumps(api_data, indent=4), content_type="application/json")
