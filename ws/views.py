import json
from datetime import datetime, UTC

from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
from django_celery_beat.models import PeriodicTask, PeriodicTasks

from phase10.models import Phase, PhasePlayers, PhaseStatus
from phase10.serializers import PhaseUserSerializer
from whoiam.models import WhoIam, WhoIamPlayers
from whoiam.serializers import WhoIamUserSerializer
from ws.consumer import WebsocketConnection


class PhaseWebsocketConsumer(WebsocketConnection):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        game = Phase.objects.get(id=self.room_name)

        user, _ = PhasePlayers.objects.update_or_create(phase=game, user=self.scope["user"], defaults={"connected": True})
        self.room_group_name = f"phase_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()  # принять соединение

        payload = {
            "event": "connect_to_room",
            "payload": PhaseUserSerializer(user).data,
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {"type": "send_message", "message": json.dumps(payload, cls=DjangoJSONEncoder)},
        )

        game.save()

    def receive(self, text_data, **kwargs):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        game = Phase.objects.get(id=self.room_name)
        if text_data_json.get("event") == "put_card":
            insert_card = game.put_card(text_data_json["payload"], self.scope["user"])
            text_data_json["payload"]["cardDraggable"] = insert_card["draggable"]
        if text_data_json.get("event") == "change_queue":
            PeriodicTask.objects.filter(task="phase10.tasks.change_queue_after_time_left").update(enabled=False)
            PeriodicTasks.update_changed()
            text_data_json["payload"] = game.change_queue()
        if text_data_json.get("event") == "finish_level":
            PhasePlayers.objects.filter(phase=game, user=self.scope["user"]).update(
                finish_level=True, finish_at=datetime.now(UTC)
            )
            player = PhasePlayers.objects.get(phase=game, user=self.scope["user"])
            complete = player.complete
            for block in complete:
                for card in block:
                    card["draggable"] = False
            player.complete = complete
            player.save(update_fields=["complete"])
        if text_data_json.get("event") == "finish_round":
            game.finish_round()
        text_data = json.dumps(text_data_json)
        super().receive(text_data, **kwargs)

    def disconnect(self, close_code):
        game = Phase.objects.get(id=self.room_name)
        if game.status == PhaseStatus.STARTED:
            PhasePlayers.objects.filter(phase=game, user=self.scope["user"]).update(connected=False)
        else:
            PhasePlayers.objects.filter(phase=game, user=self.scope["user"]).delete()
        check = PhasePlayers.objects.filter(phase=game, connected=True).count()
        # if check == 0:
        #     game.delete()
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
        payload = {
            "event": "left_from_room",
            "payload": {"user": self.scope["user"].id},
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {"type": "send_message", "message": json.dumps(payload, cls=DjangoJSONEncoder)},
        )


class WhoIamWebsocketConsumer(WebsocketConnection):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        game = WhoIam.objects.get(id=self.room_name)

        user, _ = WhoIamPlayers.objects.get_or_create(whoiam=game, user=self.scope["user"], defaults={})
        self.room_group_name = f"whoiam_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()  # принять соединение

        payload = {
            "event": "connect_to_room",
            "payload": WhoIamUserSerializer(user).data,
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {"type": "send_message", "message": json.dumps(payload, cls=DjangoJSONEncoder)},
        )

        game.save()

    def receive(self, text_data, **kwargs):
        # text_data_json = json.loads(text_data)
        # game = Phase.objects.get(id=self.room_name)
        #
        # text_data = json.dumps(text_data_json)
        super().receive(text_data, **kwargs)

    def disconnect(self, close_code):
        game = WhoIam.objects.get(id=self.room_name)
        WhoIamPlayers.objects.filter(whoiam=game, user=self.scope["user"]).update(connected=False)
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
