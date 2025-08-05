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
    pending = models.BooleanField(default=True)

    def start_game(self):
        self.start = True
        players = list(WhoIamPlayers.objects.filter(whoiam=self).order_by("created_at"))
        for idx, player in enumerate(players):
            if len(players) - 1 == idx:
                player.for_user = players[0].user
            else:
                player.for_user = players[idx+1].user
            player.word = ""
            player.create_word = False
            player.complete = False
            player.save()
        self.save()


class WhoIamPlayers(UUIDModel):
    whoiam = models.ForeignKey(WhoIam, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="who_iam_user")
    active = models.BooleanField(default=True)
    complete = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    word = models.CharField(max_length=100, null=True, blank=True)
    create_word = models.BooleanField(default=False)
    for_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="who_iam_for_user"
    )
