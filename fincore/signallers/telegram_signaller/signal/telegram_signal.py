from datetime import datetime

from fincore.signal import Signal, SignalType
from telethon import events

class TelegramSignal(Signal):

    def __init__(self, signal_time: datetime, msg_event: events.NewMessage):
        super().__init__(signal_time)
        self.msg_event = msg_event


    def get_msg_event(self)-> events.NewMessage:
        return self.msg_event

    def get_signal_type(self) -> SignalType:
        return SignalType.ORDER

    def get_source(self) -> str:
        return 'Telegram'