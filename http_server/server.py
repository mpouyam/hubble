from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from functools import wraps
import uvicorn
import os 


def api_key_required(func):
    @wraps(func)
    async def wrapper(*args, api_key: str = Header(...), **kwargs):
        if api_key != os.getenv('api_key'):
            raise HTTPException(status_code = 401, detail = 'Unauthorized')
        return await func(*args, **kwargs)
    return wrapper

class Command(BaseModel):
    command: str

class HTTPServer():

    def __init__(self, port = 3000):
        self.port = port 

    def run(self):
        app = FastAPI()
        @app.post("/command/")
        @api_key_required
        async def execute_command(command: Command):
            return ''
        uvicorn.run(app, host='0.0.0.0', port = self.port)

