import json
import uuid
import random

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.conf import settings

from utils.base_model import UUIDModel


def generate_code():
    return uuid.uuid4().hex[:4]


def generate_deck():
    deck = []
    colors = ["red", "blue", "green", "yellow"]
    for i in range(1, 13):
        for color in colors:
            deck.append({"id": f"{color}{i}_1", "color": color, "number": i, "draggable": True})
            deck.append({"id": f"{color}{i}_2", "color": color, "number": i, "draggable": True})
    for count, card in [(8, "star"), (4, "cancel")]:
        for i in range(count):
            deck.append({"id": f"{card}_{i + 1}", "color": card, "number": card, "draggable": True})
    return deck


class Phase(UUIDModel):
    code = models.CharField(max_length=4, unique=True, default=generate_code)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="phase_game")
    start = models.BooleanField(default=False)
    deck = ArrayField(models.JSONField(), default=list)
    discard = ArrayField(models.JSONField(), default=list)

    def start_game(self):
        deck = generate_deck()
        random.shuffle(deck)
        order_by = "finish_at" if self.start else "created_at"
        players = PhasePlayers.objects.filter(phase=self).order_by(order_by)
        for idx, player in enumerate(players):
            player.hand = deck[idx * 10: (idx + 1) * 10]
            player.current_queue = idx == 0
            player.finish_at = None
            player.complete = [[]] if player.level in [4, 5, 6, 8] else [[], []]
            player.save()
        self.discard = [deck[(len(players) * 10)]]
        if self.discard[0]["number"] == "cancel" and players.count() > 1:
            for idx, player in enumerate(players):
                if idx == 0:
                    player.current_queue = False
                elif idx == 1:
                    player.current_queue = True
                else:
                    break
                player.save()
        self.deck = deck[(len(players) * 10) + 1:]
        self.start = True
        self.save()


    def put_card(self, payload):
        if payload["from_user"] == "game":
            if payload["from_group"] == "deck":
                self.deck = [card for card in self.deck if card["id"] != payload["cardId"]]
            else:
                self.discard = [card for card in self.discard if card["id"] != payload["cardId"]]
        else:
            player = PhasePlayers.objects.get(phase=self, user_id=payload["from_user"])
            if payload["from_group"] == "hand":
                player.hand = [card for card in player.hand if card["id"] != payload["cardId"]]
            else:
                group, index = payload["from_group"].split("_")
                player.complete[int(index)] = [card for card in player.complete[int(index)] if
                                               card["id"] != payload["cardId"]]
            player.save()

        insert_card = {"id": payload["cardId"], "color": payload["cardColor"], "number": payload["cardNumber"],
                       "draggable": payload["cardDraggable"]}

        if payload["to_user"] == "game":
            if payload["to_group"] == "discard":
                self.discard.insert(0, insert_card)
        else:
            player = PhasePlayers.objects.get(phase=self, user_id=payload["to_user"])
            if payload["to_group"] == "hand":
                player.hand.insert(payload["index"], insert_card)
            else:
                if payload["from_user"] != "game":
                    if payload["from_user"] != payload["to_user"]:
                        insert_card["draggable"] = False
                    else:
                        insert_card["draggable"] = not player.finish_level
                group, index = payload["to_group"].split("_")
                player.complete[int(index)].insert(payload["index"], insert_card)

            player.save()
        self.save()
        return insert_card

    def change_queue(self):
        order_by = "finish_at" if self.start else "created_at"
        players = PhasePlayers.objects.filter(phase=self).order_by(order_by)
        next_player, player_id, cancel, break1 = False, None, False, False

        while True:
            if break1:
                break
            for player in players:
                if player.current_queue:
                    player.current_queue = False
                    player.save()
                    next_player = True
                    continue
                if next_player:
                    if self.discard[0]["number"] == "cancel" and not cancel:
                        cancel = True
                        continue
                    player.current_queue = True
                    player.save()
                    player_id = player.id
                    break1 = True
                    break
        return {"user": str(player_id)}

    def finish_round(self):
        players = PhasePlayers.objects.filter(phase=self).order_by("finish_at")
        print('finish round')
        for idx, player in enumerate(players):
            print(player.user.username, idx==0)
            player.current_queue = idx == 0
            if player.finish_level:
                player.level = player.level + 1
            player.hand = []
            player.complete = []
            player.finish_level = False
            player.save()


class PhasePlayers(UUIDModel):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    hand = ArrayField(models.JSONField(), default=list)
    complete = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    current_queue = models.BooleanField(default=False)
    finish_level = models.BooleanField(default=False)
    finish_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
