from django.contrib.auth.decorators import login_required
from assetsData.models import profile
from django.shortcuts import redirect
from django.http import JsonResponse

def check_role(role='EMPLOYEE', redirect_to = 'NotFound'):
    def wrap(func):
        @login_required
        def inner1(*args, **kwargs):
            user = args[0].user
            user_department = profile.objects.get(user = user).login_type
            if user_department == role:
                return func(*args, **kwargs)
            else:
                return redirect(redirect_to)
        return inner1
    return wrap


def check_role_ajax(role='employee'):
    def wrap(func):
        @login_required
        def inner1(*args, **kwargs):
            user = args[0].user
            user_department = profile.objects.get(user = user).department.name
            if user_department == role:
                return func(*args, **kwargs)
            else:
                return JsonResponse({"status":"Prohibited"})
        return inner1
    return wrap