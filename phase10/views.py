import json

import channels.layers
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .serializers import PhaseSerializer, PhaseCustomLevelSerializer

from phase10.models import Phase, PhaseCustomLevels

channel_layer = channels.layers.get_channel_layer()


class PhaseViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "code"

    @action(methods=["POST"], detail=True, url_path="start-game")
    def start_game(self, request, code=None):
        event = request.data.get("event", "start_game")
        phase = self.get_object()
        phase.start_game()
        phase = self.get_object()
        payload = PhaseSerializer(phase).data

        async_to_sync(channel_layer.group_send)(
            f"phase_{phase.id}",
            {"type": "send_message", "message": json.dumps({"event": event, "payload": payload}, cls=DjangoJSONEncoder)},
        )
        return Response(payload, status=200)


class PhaseCustomLevelViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = PhaseCustomLevelSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PhaseCustomLevels.objects.filter(user=self.request.user).order_by("created_at")
