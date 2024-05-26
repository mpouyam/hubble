from strategies import Trader
from repository import BoxRepositoryInterface


class TraderMock(Trader):
    def __init__(self , provider , logger , repository:BoxRepositoryInterface , config) -> None:
        super().__init__(provider , logger , repository, config)
        self.handle_signal("ON")

    def _tp_action(self):
        super()._tp_action()
        self.handle_signal("ON")
