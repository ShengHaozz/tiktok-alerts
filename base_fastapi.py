from fastapi import FastAPI
from uvicorn import Config, Server
import logging

import asyncio

class App:
    def __init__(self):
        self._app = FastAPI()
        self.logger = logging.getLogger(__name__)
    
    @property
    def fastapi_app(self):
        return self._app


class Service:
    def __init__(self, app:App):
        self._app_instance = app
        config = Config(app=app.fastapi_app)
        self.server = Server(config)

    @property
    def app_instance(self):
        return self._app_instance
    
    async def _run(self):
        await self.server.serve()

    async def _stop(self):
        self.server.should_exit = True

    async def task_wrapper(self, afunc, afunc_args:list|None=None):
        fastapi_task = asyncio.create_task(self._run())
        output = await (afunc(*afunc_args) if afunc_args else afunc())
        await self._stop()
        await fastapi_task
        return output
