from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.db import models

from utils.base_model import UUIDModel


# Create your models here.

class User(AbstractBaseUser, PermissionsMixin, UUIDModel):

    username = models.CharField(max_length=255)
    apple_id = models.CharField(max_length=255, unique=True)

    objects = UserManager()
    EMAIL_FIELD = "apple_id"
    USERNAME_FIELD = "apple_id"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

