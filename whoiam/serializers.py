from rest_framework import serializers

from users.models import User
from users.serializers import UserSerializer
from .models import WhoIam, WhoIamPlayers


class WhoIamUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = WhoIamPlayers
        fields = "__all__"


class WhoIamSerializer(serializers.ModelSerializer):
    admin = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())  # Auto-set admin
    players = WhoIamUserSerializer(many=True, read_only=True)

    class Meta:
        model = WhoIam
        fields = "__all__"  # Include all fields
