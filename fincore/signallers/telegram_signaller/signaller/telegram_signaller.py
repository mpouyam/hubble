import asyncio
import datetime
from pathlib import Path
from threading import Lock
from typing import Self, Callable, Dict, Coroutine
from telethon import TelegramClient, events

from fincore.signaller import EventLoopSignaller
from fincore.signaller.signaller import SignallerStatus
from fincore.signallers.telegram_signaller.chat import ChatHandler
from fincore.signallers.telegram_signaller.signal import TelegramSignal


class TelegramSignallerConfig:
    def __init__(self, api_id: int, api_hash: str, session_path: Path):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path


class TelegramSignaller(EventLoopSignaller):


    def is_ready(self) -> bool:
        with self.ready_lock:
            return self.ready

    def set_ready(self, ready: bool):
        with self.ready_lock:
            self.ready = ready


    def __init__(self, config: TelegramSignallerConfig):
        super().__init__()
        self.config = config
        self.ready = False
        self.ready_lock = Lock()
        self.client: TelegramClient = TelegramClient(
            config.session_path,
            config.api_id,
            config.api_hash,
            loop=self.get_event_loop()
        )
        self.chandlers: Dict[ChatHandler, Callable[[events.NewMessage], Coroutine]] = dict()


    def process(self):
        asyncio.set_event_loop(self.get_event_loop())
        self.client.start()
        self.get_event_loop().call_soon_threadsafe(
            lambda : self.set_ready(True)
        )
        self.get_event_loop().run_forever()



    def stop(self):
        self.get_event_loop().stop()
        self.set_status(SignallerStatus.STOPPED)


    @staticmethod
    def decorate_handler(handler: ChatHandler)-> Callable[[events.NewMessage], Coroutine]:
        async def handle(tg_message: events.NewMessage):
            tg_signal =  TelegramSignal(
                datetime.datetime.now(),
                tg_message
            )
            await handler.handle_signal(tg_signal)
        return handle


    def subscribe_handler(self, handler: ChatHandler) -> Self:
        decorated_handler = self.decorate_handler(handler)
        self.chandlers[handler] = decorated_handler

        self.client.add_event_handler(
            decorated_handler,
            events.NewMessage(
                chats=handler.get_channel().get_id(),
                incoming=True
            )
        )
        return self


    def unsubscribe_handler(self, handler: ChatHandler) -> Self:
        if handler in self.chandlers.keys():
            self.client.remove_event_handler(self.chandlers[handler])
            self.chandlers.pop(handler)
        return self


    # def unsubscribe_chandler(
    #         self,
    #         chandler_id: str | None = None,
    #         chandler: ChatHandler | None = None
    # ) -> Self:
    #
    #     if chandler is None and chandler_id is None:
    #         raise ValueError('Either chandler or chandler_id should be provided')
    #
    #     if chandler is not None:
    #         self.chandlers.remove(chandler)
    #         self.client.remove_event_handler(chandler.handle_message)
    #     else:
    #         for chandler in self.chandlers:
    #             if chandler.get_id() == chandler_id:
    #                 self.chandlers.remove(chandler)
    #                 self.client.remove_event_handler(chandler.handle_message)
    #                 break
    #     return self

    def get_chandlers(self) -> Dict[ChatHandler, Callable[[events.NewMessage], None]]:
        return self.chandlers


    def get_client(self) -> TelegramClient:
        return self.client



    def get_signaller_name(self):
        return 'Telegram Signaller'
