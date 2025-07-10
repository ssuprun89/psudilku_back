from rest_framework import serializers

from users.models import User
from users.serializers import UserSerializer
from .models import Phase, PhasePlayers


class PhaseUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = PhasePlayers
        fields = "__all__"


class PhaseSerializer(serializers.ModelSerializer):
    admin = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())  # Auto-set admin
    players = PhaseUserSerializer(many=True, read_only=True)

    def get_players(self, obj):
        return [UserSerializer(player.user).data for player in obj.players.all()]

    class Meta:
        model = Phase
        fields = "__all__"  # Include all fields
