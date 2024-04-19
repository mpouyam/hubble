import json
import MetaTrader5 as mt5
from engine import Engine, EngineConfig, TickListener
from strategies import BeanStrategy
f = open("config.json")
conf = json.load(f)
f.close()



if mt5.initialize(
            path= conf['path'],
            login= conf['login'],
            password= conf['password'],
            server= conf['server'],
    ):
    print("MT5 Initialized Successfuly.")
else:
    raise Exception("MT5 Initialization Failed!")


engine_config = EngineConfig({
    'symbol': conf['symbol'],
    'max_stored_ticks': conf['max_stored_ticks'],
    'max_subs': conf['max_subs'],
    'period' : conf['period']
})
engine = Engine(engine_config, mt5)


test_strategy = BeanStrategy(mt5 ,conf['symbol'] )

engine.add_tick_listener(test_strategy)
test_strategy.start()
engine.start()


