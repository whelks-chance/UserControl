import json

import datetime
from django.http import HttpResponse
from django.shortcuts import render
import uuid
import subprocess
import sys
import crypt

# Create your views here.
from UserControl.settings import ACCOUNT_TIMEOUT_SECONDS, README_MSG
from usercontroller import models


def remove_openssh_user(db_user):
    assert isinstance(db_user, models.User)
    username = db_user.username
    ssh = subprocess.Popen(["sudo",
                           "/home/usercontroller/remsftpuser.sh",
                           username],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    error = ssh.stderr.readlines()

    if result == []:
        error = ssh.stderr.readlines()
        print(sys.stderr, "ERROR: {}".format(error))
        return False, result, error
    else:
        print(result)
        return True, result, error


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
    error = ssh.stderr.readlines()

    if result == []:
        print(sys.stderr, "ERROR: {}".format(error))
        return False, result, error
    else:
        print(result)
        return True, result, error


def disable_user(db_user):
    assert isinstance(db_user, models.User)
    db_user.disabled = True
    db_user.save()


def disable_expired_users(request):
    active_users = []
    disabled_users = []
    users_disabled = []
    errors = []

    print(ACCOUNT_TIMEOUT_SECONDS)
    for u in models.User.objects.all():
        if not u.disabled:
            print(datetime.datetime.now(tz=datetime.timezone.utc))
            print(u.created)
            time_diff = datetime.datetime.now(tz=datetime.timezone.utc) - u.created

            print('\n', time_diff)
            print(time_diff.total_seconds())
            print(time_diff.total_seconds() > ACCOUNT_TIMEOUT_SECONDS)

            if time_diff.total_seconds() > ACCOUNT_TIMEOUT_SECONDS:
                success, result, error = remove_openssh_user(u)

                if success:
                    disable_user(u)
                    users_disabled.append(u.username)
                else:
                    if len(error):
                        if 'does not exist' in error[0]:
                            errors.append("System user {} does not exist, disabling user in DB.".format(u.username))
                            disable_user(u)
                    else:
                        errors.append("Failed to remove system user {}.".format(u.username))
            else:
                active_users.append(u.username)
        else:
            disabled_users.append(u.username)

    api_data = {
        'README': README_MSG.format(ACCOUNT_TIMEOUT_SECONDS),
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
