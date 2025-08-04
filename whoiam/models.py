import uuid

from django.db import models
from django.conf import settings

from utils.base_model import UUIDModel


def generate_code():
    return uuid.uuid4().hex[:4]


class WhoIam(UUIDModel):
    code = models.CharField(max_length=4, unique=True, default=generate_code)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="who_iam_game")
    start = models.BooleanField(default=False)


class WhoIamPlayers(UUIDModel):
    whoiam = models.ForeignKey(WhoIam, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    complete = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    word = models.CharField(max_length=100)
