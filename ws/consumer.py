from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class WebsocketConnection(WebsocketConsumer):
    def connect(self):
        pass

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data, **kwargs):
        message = text_data
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "send_message", "message": message})

    def send_message(self, event):
        message = event["message"]
        self.send(text_data=message)
