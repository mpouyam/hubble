from abc import abstractmethod
from uuid import uuid4
from telethon import events
from finwave.fincore.signallers.telegram_signaller.chat import Chat
from finwave.fincore.signallers.telegram_signaller.signal import TelegramSignalHandler


class ChatHandler(TelegramSignalHandler):
    def __init__(self, channel: Chat):
        self.channel = channel
        self.id = str(uuid4())

    def get_id(self)-> str:
        return self.id

    def get_channel(self) -> Chat:
        return self.channel


    @abstractmethod
    def handle_message(self, message: events.NewMessage):
        pass


