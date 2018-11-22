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

    # "sudo /home/usercontroller/remsftpuser.sh username"
    rem_user_proc = subprocess.Popen(["sudo",
                           "/home/usercontroller/remsftpuser.sh",
                           username],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    rem_user_proc.wait()
    result = rem_user_proc.stdout.readlines()
    error = rem_user_proc.stderr.readlines()

    if result == []:
        print("ERROR: {}: {}".format(result, error))
        return False, result, error
    else:
        print("SUCCESS: {}: {}".format(result, error))
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
        print("ERROR: {}".format(error))
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
    activities = []

    print("Max account age is {} seconds".format(ACCOUNT_TIMEOUT_SECONDS))
    for u in models.User.objects.all():
        activity_dict = {
            'USERNAME': u.username,
            'START_DISABLED': u.disabled
        }
        if not u.disabled:
            time_now = datetime.datetime.now(tz=datetime.timezone.utc)
            print('\nTime now {}'.format(time_now))
            activity_dict['TIME_NOW'] = str(time_now)

            print('Time user created {}'.format(
                u.created
            ))
            activity_dict['USER_CREATED'] = str(time_now)

            time_diff = time_now - u.created
            print('Account age {} seconds'.format(time_diff.total_seconds()))
            activity_dict['ACCOUNT_AGE'] = time_diff.total_seconds()

            should_disable_account = time_diff.total_seconds() > ACCOUNT_TIMEOUT_SECONDS
            activity_dict['SHOULD_DISABLE'] = should_disable_account

            if should_disable_account:
                disable_log = []
                print('Account will be disabled.')
                success, result, error = remove_openssh_user(u)

                if success:
                    disable_log.append('Successfully removed system user.')
                    disable_user(u)
                    disable_log.append('Successfully disabled user profile.')
                    users_disabled.append(u.username)
                else:
                    disable_log.append("Failed to remove system user {}".format(u.username))

                    if len(error):
                        if b'does not exist' in error[0]:
                            disable_log.append("System user {} does not exist.")
                            disable_log.append("Disabling user in DB.".format(u.username))
                            disable_user(u)
                            disable_log.append('Successfully disabled user profile.')
                        else:
                            disable_log.append("Error: {}".format(error))
                            disable_log.append("User {} will remain active.".format(u.username))
                            active_users.append(u.username)
                    else:
                        disable_log.append("No error discription available")
                        disable_log.append("User {} will remain active.".format(u.username))
                        active_users.append(u.username)

                activity_dict['DISABLE_LOG'] = disable_log
            else:
                print('Account will remain enabled.')
                active_users.append(u.username)
        else:
            disabled_users.append(u.username)
        activities.append(activity_dict)

    api_data = {
        'README': README_MSG.format(ACCOUNT_TIMEOUT_SECONDS),
        'active_users': active_users,
        'disabled_users': disabled_users,
        'users_disabled': users_disabled,
        'activities': activities
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
