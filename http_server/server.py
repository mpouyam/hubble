from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from backtest import back_test
import uvicorn
from config import RulesConfig, TraderConfigCalculator
from news import NewsManager, NewsService
from type import TraderSignal
from typing import Optional
from strategy import TraderManager
from dotenv import load_dotenv
from http_server import HubbleHttpController
import os

def api_key_auth(api_key: str = Header(...)):
    if api_key != os.getenv('api_key'):
        raise HTTPException(status_code=401, detail='Unauthorized')


class Command(BaseModel):
    command: str


class HubbleHttpController():

    def __init__(self, trader: TraderManager, port=3000):
        self.trader = trader
        self.port = port

    async def execute_command(self, command: Command):
        command = command.command

        result = None
        try:
            if command == 'GET_STATUS':
                result = self.trader.get_all_status()

            elif command == 'TURN_OFF':
                self.trader.handle_signal(TraderSignal.OFF)
                result = self.trader.get_all_status()

            elif command == 'TURN_OFFF':
                self.trader.handle_signal(TraderSignal.OFFF)
                result = self.trader.get_all_status()

            elif command == 'TURN_ON':
                self.trader.handle_signal(TraderSignal.ON)
                result = self.trader.get_all_status()

            elif command == 'PAUSE':
                self.trader.handle_signal(TraderSignal.PAUSE)
                result = self.trader.get_all_status()

            elif command == 'RESUME':
                self.trader.handle_signal(TraderSignal.RESUME)
                result = self.trader.get_all_status()


            else:
                raise Exception("Unknown Command")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Bad Request - {e.args[0]}')

        return {"result": result}

    def run(self):
        app = FastAPI()

        @app.post("/command/", dependencies=[Depends(api_key_auth)])
        async def execute_command(command: Command):
            return await self.execute_command(command)

        @app.post("/config", dependencies=[Depends(api_key_auth)])
        async def change_config(params: Optional[TraderConfigCalculator]):
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
                result = back_test(start_date_tuple, end_date_tuple, params.config)
                return result

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/")
        async def is_alive():
            return "HTTP Server is alive and ready to receive commands"

        uvicorn.run(app, host='0.0.0.0', port=self.port)


class BacktestParams(BaseModel):
    start_date: str
    end_date: str
    config: TraderConfigCalculator
