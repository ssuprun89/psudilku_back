import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder

from phase10.models import PhasePlayers, Phase
from psudilku.celery import app


@app.task
def change_queue_after_time_left(**kwargs):
    code = kwargs["code"]
    game = Phase.objects.get(code=code)
    player = PhasePlayers.objects.get(phase=game, current_queue=True)
    channel_layer = get_channel_layer()

    if player.get_card:
        group, card = ("hand", player.hand[0]) if len(player.hand) > 0 else ("complete_0", player.complete[0][0])
        payload = {
            "from_user": player.user.id,
            "from_group": group,
            "cardId": card["id"],
            "cardColor": card["color"],
            "cardNumber": card["number"],
            "cardDraggable": True,
            "to_user": "game",
            "to_group": "discard",
            "currentUser": player.user.id,
            "index": 0,
            "time_left": 1,
        }
        game.put_card(payload, player.user)
        async_to_sync(channel_layer.group_send)(
            f"phase_{game.id}",
            {
                "type": "send_message",
                "message": json.dumps({"event": "put_card", "payload": payload}, cls=DjangoJSONEncoder),
            },
        )
    async_to_sync(channel_layer.group_send)(
        f"phase_{game.id}",
        {
            "type": "send_message",
            "message": json.dumps({"event": "change_queue", "payload": game.change_queue()}, cls=DjangoJSONEncoder),
        },
    )
