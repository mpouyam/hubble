from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from strategies import Trader, Signal
import uvicorn
import os 



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


        @app.get("/")
        async def is_alive():
            return "HTTP Server is alive and ready to receive commands"

        uvicorn.run(app, host='0.0.0.0', port = self.port)

        
