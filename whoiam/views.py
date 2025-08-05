import json

import channels.layers
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .serializers import WhoIamSerializer, WhoIamUserSerializer

from .models import WhoIam, WhoIamPlayers

channel_layer = channels.layers.get_channel_layer()


class WhoIamViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin):
    queryset = WhoIam.objects.all()
    serializer_class = WhoIamSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "code"

    @action(methods=["POST"], detail=True, url_path="start-game")
    def start_game(self, request, code=None):
        data = request.data
        game = self.get_object()
        game.start_game()
        game = self.get_object()
        payload = WhoIamSerializer(game).data

        async_to_sync(channel_layer.group_send)(
            f"whoiam_{game.id}",
            {"type": "send_message", "message": json.dumps({"event": data.get("event", "start_game"), "payload": payload}, cls=DjangoJSONEncoder)},
        )
        return Response(payload, status=200)


class WhoIamPlayersViewSet(GenericViewSet, UpdateModelMixin):
    queryset = WhoIamPlayers.objects.all()
    serializer_class = WhoIamUserSerializer
    permission_classes = [IsAuthenticated]
