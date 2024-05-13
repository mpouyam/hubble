from abc import ABC, abstractmethod
from typing import Any, Dict
import json
from enum import Enum
from uuid import UUID

class BoxRepositoryInterface(ABC):
    @abstractmethod
    def save_box_data(self, box_data: Dict[str, Any]) -> None:
        pass
 
    # @abstractmethod
    # def load_box_data(self) -> Dict[str, Any]:
    #     pass


class JSONBoxRepository(BoxRepositoryInterface):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_box_data(self, box_data: Dict[str, Any]) -> None:
        with open(self.file_path, 'r+') as f:
            try:
                data = json.load(f)  # Load existing data
                if not isinstance(data, list):  # If loaded data is not a list, initialize it as an empty list
                    data = []
            except json.JSONDecodeError:
                data = []  # Initialize data as an empty list if file is empty or not in JSON format


            data.append({**box_data})  # Append new box data object to the list
            f.seek(0)  # Move cursor to the beginning of the file
            json.dump(data, f, indent=4, cls=MyEncoder)  # Write updated data
            f.truncate()  # Truncate any remaining content (if any)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.key  # Use enum's key
        elif isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)