from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    point: float
    base: str
    quote: str
