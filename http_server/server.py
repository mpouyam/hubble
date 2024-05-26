from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from strategies import Trader, Signal
from backtest import back_test
from strategies import Config , OrdersConfig , TraderConfig
import uvicorn
import os 
import json
from datetime import datetime
from typing import Optional



def api_key_auth(api_key: str = Header(...)):
    if api_key != os.getenv('api_key'):
        raise HTTPException(status_code = 401, detail = 'Unauthorized')
    
class Command(BaseModel):
    command: str

class HubbleHttpController():

    def __init__(self, trader: Trader, port = 3000):
        self.trader = trader
        self.port = port 


    async def execute_command(self, command: Command):
        command = command.command

        result = None
        try:
            if  command == 'GET_STATUS':
                result = self.trader.get_all_status()

            elif command == 'TURN_OFF':
                self.trader.handle_signal(Signal.OFF) 
                result =  self.trader.get_all_status()

            elif command == 'TURN_OFFF':
                self.trader.handle_signal(Signal.OFFF) 
                result =  self.trader.get_all_status()
    
            elif command == 'TURN_ON':
                self.trader.handle_signal(Signal.ON)
                result =  self.trader.get_all_status()

            elif command == 'PAUSE':
                self.trader.handle_signal(Signal.PAUSE)
                result =  self.trader.get_all_status()

            elif command == 'RESUME':
                self.trader.handle_signal(Signal.RESUME)
                result =  self.trader.get_all_status()


            else:
                raise Exception("Unknown Command")
        except Exception as e:
            raise HTTPException(status_code=400, detail = f'Bad Request - {e.args[0]}')

        
        return {"result" : result}


    def run(self):
        app = FastAPI()


        @app.post("/command/", dependencies=[Depends(api_key_auth)])
        async def execute_command(command: Command):
            return await self.execute_command(command)

        @app.post("/config", dependencies=[Depends(api_key_auth)])
        async def change_config(params:Optional[Config]):
            # new_config = validate_config(params)
            self.trader.change_config(params)
            return "Done"

        @app.post("/backtest")
        async def backtest(params: BacktestParams):
            try:
                # dates = split_into_weeks(params.start_date, params.end_date)
                start_date_parts = params.start_date.split("-")
                start_date_tuple = tuple(map(int, start_date_parts))

                end_date_parts = params.end_date.split("-")
                end_date_tuple = tuple(map(int, end_date_parts))


                # for date in dates: 

                back_test(start_date_tuple , end_date_tuple , params.config)


                result = analyzer()
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/")
        async def is_alive():
            return "HTTP Server is alive and ready to receive commands"

        uvicorn.run(app, host='0.0.0.0', port = self.port)

        
class BacktestParams(BaseModel):
    start_date: str
    end_date: str
    config: Config



def analyzer():

    # Step 1: Read the JSON file
    file_path = "backtest_repo.json"
    with open(file_path, mode="r+" ,  encoding='utf-8', errors='ignore') as file:
        data = json.load(file)


    box_durations = []
    order_durations = []
    for item in data:
        box_start_time = datetime.fromisoformat(item['started_at'])
        box_end_time = datetime.fromisoformat(item['ended_at'])
        box_duration = (box_end_time - box_start_time).total_seconds() / 60  # Convert to minutes
        box_durations.append(box_duration)
        
        for order in item['orders']:
            order_start_time = datetime.fromisoformat(order['started_at'])
            order_end_time = datetime.fromisoformat(order['ended_at'])
            order_duration = (order_end_time - order_start_time).total_seconds() / 60  # Convert to minutes
            order_durations.append(order_duration)

    # Step 3: Calculate max, min, and average durations
    max_box_duration = max(box_durations)
    avg_box_duration = sum(box_durations) / len(box_durations)

    max_order_duration = max(order_durations)
    avg_order_duration = sum(order_durations) / len(order_durations)

    # Step 4: Calculate total number of boxes and max/min order number
    box_total_number = len(data)
    max_order_number = max(item['active_index'] for item in data)


    result = {
        "MAX_BOX_DURATION": round(max_box_duration),
        "AVG_BOX_DURATION": round(avg_box_duration),
        "MAX_ORDER_DURATION": round(max_order_duration),
        "AVG_ORDER_DURATION": round(avg_order_duration),
        "BOX_TOTAL_NUMBER": round(box_total_number),
        "MAX_ORDER_NUMBER": round(max_order_number),
    }   

     # Step 3: Clear the contents of the file
    # with open(file_path, "w") as file:
    #     json.dump([], file)

    # Output the result
    return result


def validate_config(json_data):
    trader_config_data = json_data.get('trader_config', {})
    orders_config_data = json_data.get('orders_config', {})
    
    trader_config = TraderConfig(
        default_working_hours=tuple(trader_config_data.get('default_working_hours', [])),
        working_hours={int(k): tuple(v) for k, v in trader_config_data.get('working_hours', {}).items()},
        default_not_working_hours=tuple(trader_config_data.get('default_not_working_hours', [])),
        not_working_hours={int(k): tuple(v) for k, v in trader_config_data.get('not_working_hours', {}).items()}
    )
    
    orders_config = OrdersConfig(
        symbol=orders_config_data.get('symbol', ''),
        first_order_signal=orders_config_data.get('first_order_signal', ''),
        pip_unit=orders_config_data.get('pip_unit'),
        try_count=orders_config_data.get('try_count', 0),
        tp_limit=orders_config_data.get('tp_limit', 0),
        sl_limit=orders_config_data.get('sl_limit', 0),
        base_lot=orders_config_data.get('base_lot', 0.0),
        growth_factor=orders_config_data.get('growth_factor', 0.0),
        static_vol={int(k): v for k, v in orders_config_data.get('static_vol', {}).items()},
        static_tp={int(k): v for k, v in orders_config_data.get('static_tp', {}).items()},
        static_sl={int(k): v for k, v in orders_config_data.get('static_sl', {}).items()}
    )
    
    return {'trader_config': trader_config, 'orders_config': orders_config}
