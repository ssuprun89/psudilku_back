import json
import uuid
import random
from datetime import datetime, UTC, timedelta
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.conf import settings

from utils.base_model import UUIDModel


class CardUtils:
    COLORS = ["red", "blue", "green", "yellow"]
    SPECIAL_CARDS = {"star": 8, "cancel": 4}

    @staticmethod
    def generate_code():
        """Generate a unique 4-character code for a phase."""
        while True:
            code = uuid.uuid4().hex[:4]
            if not Phase.objects.filter(code=code).exists():
                return code

    @staticmethod
    def generate_deck():
        """Generate a complete game deck with regular and special cards."""
        deck = []
        # Regular cards: numbers 1-12, four colors, two copies each
        for number in range(1, 13):
            for color in CardUtils.COLORS:
                for copy in (1, 2):
                    deck.append({"id": f"{color}{number}_{copy}", "color": color, "number": number, "draggable": True})
        # Special cards: star and cancel
        for card_type, count in CardUtils.SPECIAL_CARDS.items():
            for i in range(1, count + 1):
                deck.append({"id": f"{card_type}_{i}", "color": card_type, "number": card_type, "draggable": True})
        return deck

    @staticmethod
    def create_card_from_payload(payload):
        """Create a card object from payload data."""
        return {
            "id": payload["cardId"],
            "color": payload["cardColor"],
            "number": payload["cardNumber"],
            "draggable": payload["cardDraggable"],
        }


class PhaseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    STARTED = "started", "Started"
    FINISHED = "finished", "Finished"


class Phase(UUIDModel):
    code = models.CharField(max_length=4, unique=True, default=CardUtils.generate_code)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="phase_game")
    status = models.CharField(choices=PhaseStatus.choices, default=PhaseStatus.PENDING)
    deck = ArrayField(models.JSONField(), default=list)
    discard = ArrayField(models.JSONField(), default=list)
    round = models.IntegerField(default=1)
    level_config = models.JSONField(default=dict)
    duration = models.IntegerField(default=60)
    change_queue_time = models.DateTimeField(auto_created=True, null=True)

    def start_game(self):
        """Initialize a new game phase with deck and player setup."""
        self.deck = CardUtils.generate_deck()
        random.shuffle(self.deck)
        players = self._get_ordered_players()
        in_game = players.filter(in_game=True)
        self._distribute_cards(players)
        self._initialize_discard(in_game)
        self._handle_cancel_card(in_game)

        self.status = PhaseStatus.STARTED
        self.change_queue_time = datetime.now(UTC)
        self.save()

    def _get_ordered_players(self):
        """Get players ordered by finish time or creation time."""
        order_by = "finish_at" if self.status == PhaseStatus.STARTED else "created_at"
        return PhasePlayers.objects.filter(phase=self).order_by("in_game", order_by)

    def _distribute_cards(self, players):
        """Distribute initial cards to players."""
        for idx, player in enumerate(players):
            if player.in_game:
                player.hand = self.deck[idx * 10 : (idx + 1) * 10]
                player.current_queue = idx == 0
            player.order_queue = idx
            player.finish_at = None
            player.get_card = False
            player.put_card = False
            player.complete = (
                [[]] if len(self.level_config.get(str(player.level), {"rules": [1]})["rules"]) == 1 else [[], []]
            )
            player.save()

    def _initialize_discard(self, players):
        """Initialize discard pile with first card."""
        self.discard = [self.deck[len(players) * 10]]
        self.deck = self.deck[len(players) * 10 + 1 :]

    def _handle_cancel_card(self, players):
        """Handle special case for cancel card in discard pile."""
        if self.discard[0]["number"] == "cancel" and players.count() > 1:
            for idx, player in enumerate(players):
                player.current_queue = idx == 1
                player.save()
                if idx >= 1:
                    break

    def put_card(self, payload, current_user):
        """Handle card placement logic between game and players."""
        self._remove_card_from_source(payload)
        insert_card = CardUtils.create_card_from_payload(payload)
        self._add_card_to_destination(payload, insert_card, current_user)

        self._update_player_flags(payload, current_user)
        self.save()
        return insert_card

    def _remove_card_from_source(self, payload):
        """Remove card from source (deck, discard, or player hand/complete)."""
        if payload["from_user"] == "game":
            source = self.deck if payload["from_group"] == "deck" else self.discard
            source[:] = [card for card in source if card["id"] != payload["cardId"]]
        else:
            player = PhasePlayers.objects.get(phase=self, user_id=payload["from_user"])
            if payload["from_group"] == "hand":
                player.hand[:] = [card for card in player.hand if card["id"] != payload["cardId"]]
            else:
                group, index = payload["from_group"].split("_")
                player.complete[int(index)] = [
                    card for card in player.complete[int(index)] if card["id"] != payload["cardId"]
                ]
            player.save()

    def _add_card_to_destination(self, payload, insert_card, current_user):
        """Add card to destination (discard or player hand/complete)."""
        if payload["to_user"] == "game":
            if payload["to_group"] == "discard":
                self.discard.insert(0, insert_card)
        else:
            player = PhasePlayers.objects.get(phase=self, user_id=payload["to_user"])
            if payload["to_group"] == "hand":
                player.hand.insert(payload["index"], insert_card)
            else:
                self._handle_complete_card(payload, insert_card, player, current_user)
            player.save()

    def _handle_complete_card(self, payload, insert_card, player, current_user):
        """Handle card placement in player's complete groups."""
        if payload["from_user"] != "game":
            insert_card["draggable"] = payload["from_user"] == payload["to_user"] and not player.finish_level
        group, index = payload["to_group"].split("_")
        player.complete[int(index)].insert(payload["index"], insert_card)

    def _update_player_flags(self, payload, current_user):
        """Update player flags based on card movement."""
        if payload["from_user"] == "game" and payload["to_user"] == str(current_user.id):
            PhasePlayers.objects.filter(phase=self, user_id=current_user.id).update(get_card=True)
        if payload["to_user"] == "game" and payload["from_user"] == str(current_user.id):
            PhasePlayers.objects.filter(phase=self, user_id=current_user.id).update(put_card=True)

    def change_queue(self):
        """Advance the turn queue to the next player."""
        players = PhasePlayers.objects.filter(phase=self, in_game=True).order_by("order_queue")
        if not players.exists():
            return

        next_player, player, cancel, break1 = False, None, False, False

        while True:
            if break1:
                break
            for player in players:
                player.get_card = False
                player.put_card = False
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
                    player = player
                    break1 = True
                    break
        time_update = datetime.now(UTC)
        self.change_queue_time = time_update
        self.save()

        self._schedule_queue_change()
        return {"user": str(player.id), "u_id": str(player.user.id), "change_queue_time": time_update.timestamp()}

    def _schedule_queue_change(self):
        """Schedule the next queue change using Celery."""
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=timezone.now() + timedelta(seconds=self.duration + 5)
        )
        PeriodicTask.objects.update_or_create(
            clocked=clocked,
            task="phase10.tasks.change_queue_after_time_left",
            kwargs=json.dumps({"code": self.code}),
            one_off=True,
            enabled=True,
            name=f"change_queue|{self.code}|{int(timezone.now().timestamp())}",
        )

    def finish_round(self):
        """Complete the current round and reset player states."""
        players = self._get_ordered_players()
        for idx, player in enumerate(players):
            player.current_queue = idx == 0
            if player.finish_level:
                player.level += 1
            player.hand = []
            player.complete = []
            player.finish_level = False
            player.get_card = False
            player.put_card = False
            player.in_game = player.connected
            player.save()
        self.round += 1
        self.save()


class PhasePlayers(UUIDModel):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.IntegerField(default=0)
    hand = ArrayField(models.JSONField(), default=list)
    complete = models.JSONField(default=list)
    connected = models.BooleanField(default=True)
    in_game = models.BooleanField(default=True)
    current_queue = models.BooleanField(default=False)
    finish_level = models.BooleanField(default=False)
    finish_at = models.DateTimeField(null=True, blank=True)
    order_queue = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    get_card = models.BooleanField(default=False)
    put_card = models.BooleanField(default=False)


class PhaseCustomLevels(UUIDModel):
    DEFAULT_LEVELS = [
        {"rules": [{"condition": "all", "count": 3}, {"condition": "all", "count": 3}]},
        {"rules": [{"condition": "all", "count": 3}, {"condition": "order", "count": 4}]},
        {"rules": [{"condition": "all", "count": 4}, {"condition": "order", "count": 4}]},
        {"rules": [{"condition": "order", "count": 7}]},
        {"rules": [{"condition": "order", "count": 8}]},
        {"rules": [{"condition": "order", "count": 9}]},
        {"rules": [{"condition": "all", "count": 4}, {"condition": "all", "count": 4}]},
        {"rules": [{"condition": "color", "count": 7}]},
        {"rules": [{"condition": "all", "count": 5}, {"condition": "all", "count": 2}]},
        {"rules": [{"condition": "all", "count": 5}, {"condition": "all", "count": 3}]},
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
