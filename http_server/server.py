from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from strategies import Trader, Signal
from utils import split_into_weeks
from backtest import back_test
import uvicorn
import os 
from typing import Dict
import json



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
                result = self.trader.get_status()

            elif command == 'TURN_OFF':
                self.trader.handle_signal(Signal.OFF) 
                result =  self.trader.get_status()

            elif command == 'TURN_OFFF':
                self.trader.handle_signal(Signal.OFFF) 
                result =  self.trader.get_status()
    
            elif command == 'TURN_ON':
                self.trader.handle_signal(Signal.ON)
                result =  self.trader.get_status()

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
        
        
        @app.post("/backtest")
        async def backtest(params: BacktestParams):

            try:
                dates = split_into_weeks(params.start_date, params.end_date)
                
                for date in dates: 
                    back_test(date[0] , date[1] , params.symbol)


                result = analyzer()
                return {"message": "Backtest started successfully", "result": result }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/")
        async def is_alive():
            return "HTTP Server is alive and ready to receive commands"

        uvicorn.run(app, host='0.0.0.0', port = self.port)

        
class BacktestParams(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    first_order_signal: str
    tp_limit: int
    sl_limit: int
    base_lot: float
    growth_factor: float
    base_index: int
    static_vol: Dict[int, float]
    static_tp: Dict[int, int]
    static_sl: Dict[int, int]


def analyzer():

    # Step 1: Read the JSON file
    file_path = "backtest_repo.json"

    with open(file_path, "r") as file:
        data = json.load(file)

    # Step 2: Perform the calculations
    box_total_number = len(data)
    max_order_number = max(item["active_index"] for item in data)
    min_order_number = min(item["active_index"] for item in data)

    result = {
        "BOX_TOTAL_NUMBER": box_total_number,
        "MAX_ORDER_NUMBER": max_order_number,
        "MIN_ORDER_NUMBER": min_order_number,
    }

    # Step 3: Clear the contents of the file
    with open(file_path, "w") as file:
        json.dump([], file)

    # Output the result
    return result
