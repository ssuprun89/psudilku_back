from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.db import models

from utils.base_model import UUIDModel


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):

    username = models.CharField(max_length=255)
    apple_id = models.CharField(max_length=255, unique=True)

    objects = UserManager()
    EMAIL_FIELD = "apple_id"
    USERNAME_FIELD = "apple_id"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserGames(UUIDModel):

    class GameChoices(models.TextChoices):
        ZONE_RUSH = "zone rush"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="games")
    game = models.CharField(max_length=255, choices=GameChoices.choices)
    free_trial = models.DateTimeField(null=True)
    paid = models.BooleanField(default=False)
    apple_id = models.CharField(max_length=255)

    @classmethod
    def create_for_new_user(cls, user):
        apple_id_for_game = {
            "zone rush": "7f33b933ccb74651b833382c9a6c9e8c",
        }
        for i in cls.GameChoices.choices:
            cls(user=user, game=i[0], apple_id=apple_id_for_game[i[0]]).save()

    class Meta:
        unique_together = ("user", "game")
