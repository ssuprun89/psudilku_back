from rest_framework import serializers

from users.models import User, UserGames


class UserGamesSerializer(serializers.ModelSerializer):

    free_trial = serializers.DateTimeField(format="%s", required=False)

    class Meta:
        model = UserGames
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):

    games = UserGamesSerializer(many=True, read_only=True)

    def create(self, validated_data):
        user = User(username=validated_data["username"])
        user.set_password(validated_data["password"])  # Hashes the password
        user.save()
        return user

    class Meta:
        model = User
        fields = ("id", "username", "password", "apple_id", "games")
        extra_kwargs = {"password": {"write_only": True}}
