from abc import ABC
from typing import Self, Set

from fincore.strategy import Strategy


class Trader(ABC):
    def __init__(self):
        self.strategies: Set[Strategy] = set()


    def get_strategies(self)-> Set[Strategy]:
        return self.strategies

    def add_strategy(self, strategy: Strategy)-> Self:
        self.strategies.add(strategy)
        return self

    def remove_strategy(self, strategy: Strategy)-> Self:
        self.strategies.remove(strategy)
        return self



