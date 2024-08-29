from dataclasses import dataclass
from typing import Tuple, Dict, Optional
from type import Symbol


@dataclass
class RulesConfig:
    symbol: Symbol
    default_working_hours: Tuple[float, float]
    # working_hours: Optional[Dict[int, Tuple[float, float]]]
    before_news_minute: int
    after_news_minute: int
