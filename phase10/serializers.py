import uuid

from rest_framework import serializers

from users.models import User
from users.serializers import UserSerializer
from .models import Phase, PhasePlayers, PhaseCustomLevels

def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


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

    def validate(self, attrs):
        if attrs.get("level_config") == "default":
            level_config = PhaseCustomLevels.DEFAULT
        elif is_uuid(attrs.get("level_config")):
            level_config = PhaseCustomLevels.objects.filter(pk=attrs.get("level_config")).first()
            if not level_config:
                raise serializers.ValidationError("Level config does not exist")
            level_config = level_config.config
        else:
            raise serializers.ValidationError("Level config did not provide")

        config = {}
        for idx, level in enumerate(level_config):
            condition = "("
            for i, r in enumerate(level["rules"]):
                if i == 1:
                    condition += " + "
                if r["condition"] == "all":
                    letter = "A" if i == 0 else "B"
                    condition += letter * int(r["count"])
                elif r["condition"] == "order":
                    start = 65 if i == 0 else 75
                    condition += "".join([chr(start + n) for n in range(int(r["count"]))])
                else:
                    condition += f"color({r['count']})"
            condition += ")"

            config[idx] = {
                "levelNumber": idx + 1,
                "levelCondition": condition,
                "rules": level["rules"],
            }
        attrs["level_config"] = config
        return super().validate(attrs)


    class Meta:
        model = Phase
        fields = "__all__"  # Include all fields


class PhaseCustomLevelSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())  # Auto-set admin

    class Meta:
        model = PhaseCustomLevels
        fields = "__all__"
