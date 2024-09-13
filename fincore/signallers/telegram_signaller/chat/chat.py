from typing import Self

from telethon.tl.types import Chat as TgChat, User as TgUser, Channel as TgChannel
from typing import Union
TgEntity = Union[TgUser, TgChat, TgChannel]

class Chat:
    def __init__(self,
                 channel_id: str = None,
                 channel_username: str = None,
                 channel_name: str = None,
        ):
        if channel_id is None and channel_username is None and channel_name is None:
            raise ValueError('channel_id or channel_username or channel_name is required')
        self.id = channel_id
        self.username = channel_username
        self.name = channel_name
        self.tg_entity : TgEntity | None = None
        self.msg_regex : str | None = None



    def get_id(self) -> str | None:
        return self.id

    def get_username(self) -> str | None:
        return self.username


    def get_name(self) -> str | None:
        return self.name

    def set_name(self, name: str) -> Self:
        self.name = name
        return self

    def set_id(self, id: str) -> Self:
        self.id = id
        return self

    def set_username(self, username: str) -> Self:
        self.username = username
        return self

    def set_tg_entity(self, tg_entity: TgEntity)-> Self:
        self.tg_entity = tg_entity
        return self

    def get_tg_entity(self)-> TgEntity:
        return self.tg_entity

    def set_msg_regex(self, msg_regex: str)-> Self:
        self.msg_regex = msg_regex
        return self

    def get_msg_regex(self)-> str | None:
        return self.msg_regex



