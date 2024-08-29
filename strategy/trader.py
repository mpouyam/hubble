from config import TraderConfigCalculator, OrderConfigCalculator
from repository import BoxRepositoryInterface
from platform import Platform
from type import TraderSignal, TraderSignalData, BoxSignal , BoxSignalData,OrderDirection
from .box import BoxManager
from .rules import  Rules
from abc import ABC, abstractmethod
from publisher import TickListener

class TraderManager(TickListener):
    _state: 'TraderState' = None

    def __init__(
            self,
            provider: Platform,
            logger,
            workingRules: Rules,
            repository: BoxRepositoryInterface,
            configManager: TraderConfigCalculator
    ):

        self.should_stop = False
        self.provider = provider
        self.logger = logger
        self.time_manager = workingRules
        self.repository = repository
        self.config_manager = configManager

        self.box_manager = None
        self.transition_to(Listening())

    def transition_to(self, state: 'TraderState') -> None:
        self.logger.warning(f"TRADER Transition To: {state.__class__.__name__}")

        self._state = state
        self._state.trader_manager = self

    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:

        if signal not in TraderSignal:
            self.logger.error(f"Invalid Signal Received: {signal}")
            return

        else:
            self.logger.critical(f"\n Layer: {self.__class__.__name__}\n State: {self._state.__class__.__name__}\n Signal : {signal}")
            self._state.on_signal(signal, data)

    def on_tick(self, tick) -> None:
        self.logger.info(f"\n Layer: {self.__class__.__name__}\n State: {self._state.__class__.__name__}\n Tick : {tick}")
        self._state.on_tick(tick)

    def get_status(self) -> str:
        return "UP"

    def get_symbol(self) -> str:
        return self.config_manager.get_symbol()


class TraderState(ABC):
    _trader_manager: TraderManager = None

    @property
    def trader_manager(self) -> TraderManager:
        return self._trader_manager

    @trader_manager.setter
    def trader_manager(self, trader_manager: TraderManager) -> None:
        self._trader_manager = trader_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: TraderSignal, data) -> None:
        pass


class Listening(TraderState):
    clock: int

    def on_tick(self, tick) -> None:
        self.clock = tick[0]

    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:
        if signal == TraderSignal.SHUT_DOWN:
            self.trader_manager.transition_to(Leave())

        if signal == TraderSignal.RUN:
            should_work = self.trader_manager.time_manager.should_work(self.clock)
            if should_work:
                if self.trader_manager.box_manager is None:
                    self.trader_manager.config_manager.set_direction(data.get("direction"))
                    self.trader_manager.transition_to(Preparing())
                else:
                    self.trader_manager.transition_to(Processing())

        return


class Preparing(TraderState):

    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:
        return

    def on_tick(self, tick) -> None:
        box_recipes, orders_recipes = self.trader_manager.config_manager.get_config()
        order_calculator = OrderConfigCalculator(orders_recipes)
        self.trader_manager.box_manager = BoxManager(
            self.trader_manager.provider, self.trader_manager.logger,
            box_recipes, order_calculator
        )
        self.trader_manager.transition_to(Processing())

        return


class Processing(TraderState):
    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:
        if signal == TraderSignal.SHUT_DOWN:
            self.trader_manager.box_manager.on_signal(BoxSignal.CLOSE)
            self.trader_manager.should_stop = True

        if signal == TraderSignal.RUN:
            self.trader_manager.box_manager.on_signal(BoxSignal.RESUME , BoxSignalData(direction=data['direction']))

        return

    def on_tick(self, tick) -> None:
        box_is_done = self.trader_manager.box_manager.is_done()

        if box_is_done:
            self.trader_manager.transition_to(Finished())
        else:
            self.trader_manager.box_manager.on_tick(tick)


class Finished(TraderState):
    is_finished = False

    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:
        return

    def on_tick(self, tick) -> None:
        if self.is_finished:
            if self.trader_manager.should_stop:
                self.trader_manager.transition_to(Leave())
            else:
                self.trader_manager.transition_to(Listening())

        else:
            box_data = self.trader_manager.box_manager.get_data()
            self.trader_manager.repository.save_box_data(box_data)
            # reset order config
            self.trader_manager.box_manager = None
            self.is_finished = True


class Leave(TraderState):
    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:
        if signal == TraderSignal.ON:
            self.trader_manager.should_stop = False
            self.trader_manager.transition_to(Listening())

        return

    def on_tick(self, tick) -> None:
        return
