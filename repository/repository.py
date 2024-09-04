from abc import ABC, abstractmethod
from typing import Any, Dict, List
from config import BoxConfig
from type import Order
import json
from enum import Enum
from uuid import UUID
from dataclasses import dataclass, asdict,is_dataclass

@dataclass
class BoxData:
    id: str
    last_order: int
    started_at: str
    ended_at: str
    orders: List[Order]
    config: BoxConfig

class BoxRepositoryInterface(ABC):
    @abstractmethod
    def save_box_data(self, box_data: BoxData) -> None:
        pass


class JSONBoxRepository(BoxRepositoryInterface):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_box_data(self, box_data: BoxData) -> None:
        try:
            with open(self.file_path, 'r+') as f:
                try:
                    data: List[Dict[str, Any]] = json.load(f)
                except json.JSONDecodeError:
                    data = []

                data.append(self._convert_to_dict(box_data))
                f.seek(0)
                json.dump(data, f, indent=4, cls=CustomJSONEncoder)
                f.truncate()
        except FileNotFoundError:
            with open(self.file_path, 'w') as f:
                json.dump([self._convert_to_dict(box_data)], f, indent=4, cls=CustomJSONEncoder)

    def _convert_to_dict(self, obj: Any) -> Any:
        """Recursively convert dataclass objects to dictionaries."""
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_to_dict(value) for key, value in obj.items()}
        else:
            return obj


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Exception):
            return str(obj)
        return super().default(obj)

