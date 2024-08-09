from dataclasses import dataclass
from typing import Tuple, Dict


@dataclass
class RulesConfig:
    default_working_hours: Tuple[float, float]
    working_hours: Dict[int, Tuple[float, float]]
    default_not_working_hours: Tuple[float, float]
    not_working_hours: Dict[int, Tuple[float, float]]
    before_news_minute: int
    after_news_minute: int
