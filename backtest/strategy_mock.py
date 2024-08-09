from repository import BoxRepositoryInterface
from strategy import TraderManager


class TraderMock(TraderManager):
    def __init__(self, provider, logger, repository: BoxRepositoryInterface, config) -> None:
        super().__init__(provider, logger, repository, config)
        self.handle_signal("ON")
