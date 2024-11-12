from dataclasses import dataclass
from enum import StrEnum

from .box import BoxSignalData


@dataclass
class TraderSignalData(BoxSignalData):
    pass


class TraderSignal(StrEnum):
    RUN = "RUN"
    SHUT_DOWN = "SHUT_DOWN"
    ON = "ON"
