from abc import abstractmethod
from telethon import events

from finwave.fincore.signal_handler import SignalHandler
from finwave.fincore.signallers.telegram_signaller.signal.telegram_signal import TelegramSignal


class TelegramSignalHandler(SignalHandler):


    async def handle_signal(self, signal: TelegramSignal):
       await self.handle_message(signal.get_msg_event())


    @abstractmethod
    async def handle_message(self, msg: events.NewMessage):
        pass



