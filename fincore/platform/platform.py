from abc import ABC, abstractmethod


class Platform(ABC):

    @abstractmethod
    def get_platform_version(self):
        pass


    @abstractmethod
    def get_platform_name(self):
        pass