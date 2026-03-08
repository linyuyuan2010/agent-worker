import asyncio
import pathlib
import logging
from contextlib import asynccontextmanager

import fastapi
import aiodocker
import uvicorn

import utils
import init
import models
import middlewares

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    app.state.docker = aiodocker.Docker()
    yield
    await app.state.docker.close()

data = pathlib.Path('./data')
logger = logging.getLogger('agent_api')
app = fastapi.FastAPI(lifespan=lifespan)

if not pathlib.Path('./INSTALLED').exists():
    asyncio.run(init.init(data=data))


app.add_middleware(middlewares.AuthMiddleware)

@app.post("/create/", summary="创建一个新的 Agent", description="在 Docker 中启动一个指定的 Agent 容器")
async def create_agent(item: models.CreateRequest):
    success, container = await utils.create_agent_instance(app.state.docker, item.agent_id, item.api_url, item.sk_value)

    if not success:
        raise fastapi.exceptions.HTTPException(status_code=400, detail=models.format_response(False, "fail to create agent"))
    
    return models.format_response(True, "success")
    
@app.post("/kill/", summary="销毁一个 Agent", description="通过 agent_id 停止并移除对应的容器")
async def kill_agent(item: models.KillRequest):
    success = await utils.kill_agent_instance(app.state.docker, item.agent_id)

    if not success:
        raise fastapi.exceptions.HTTPException(status_code=400, detail=models.format_response(False, "fail to kill agent"))
    
    return models.format_response(True, "success")

@app.post("/delete/")
async def delete_agent(item: models.DeleteRequest):
    success = await utils.delete_agent_instance(app.state.docker, item.agent_id)

uvicorn.run(app)