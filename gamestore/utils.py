from django.core.exceptions import ObjectDoesNotExist
from gamestore.models import RegUser


def user_from_req(request):
    try:
        return RegUser.objects.get(user=request.user.pk)
    except ObjectDoesNotExist:
        return None


def convert_or_none(func, value):
    try:
        return func(value)
    except ValueError:
        return None
