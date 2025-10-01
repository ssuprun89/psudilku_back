import json

import channels.layers
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .serializers import PhaseSerializer, PhaseCustomLevelSerializer

from phase10.models import Phase, PhaseCustomLevels, PhaseStatus, PhasePlayers

channel_layer = channels.layers.get_channel_layer()


class PhaseViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "code"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            instance.status != PhaseStatus.PENDING
            and not PhasePlayers.objects.filter(phase=instance, user_id=request.user.id).exists()
        ):
            return Response(status=status.HTTP_404_NOT_FOUND, data={"message": "Phase already started."})
        else:
            return super().retrieve(request, *args, **kwargs)

    @action(methods=["POST"], detail=True, url_path="start-game")
    def start_game(self, request, code=None):
        event = request.data.get("event", "start_game")
        phase = self.get_object()
        phase.start_game()
        phase = self.get_object()
        payload = PhaseSerializer(phase).data

        async_to_sync(channel_layer.group_send)(
            f"phase_{phase.id}",
            {
                "type": "send_message",
                "message": json.dumps({"event": event, "payload": payload}, cls=DjangoJSONEncoder),
            },
        )
        return Response(payload, status=200)


class PhaseCustomLevelViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = PhaseCustomLevelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PhaseCustomLevels.objects.filter(user=self.request.user).order_by("created_at")
