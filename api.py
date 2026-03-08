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
import tasks
import config

logger = logging.getLogger("agent_worker")


# 管理 Docker 连接器
@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    task = asyncio.create_task(tasks.delete_expired_files())
    app.state.docker = aiodocker.Docker()
    yield
    task.cancel()
    await app.state.docker.close()


app = fastapi.FastAPI(lifespan=lifespan)

app.add_middleware(middlewares.AuthMiddleware)


@app.post(
    "/create/",
    summary="创建一个新的 Agent",
    description="在 Docker 中启动一个指定的 Agent 容器",
)
async def create_agent(item: models.CreateRequest):
    success, container = await utils.create_agent_instance(
        app.state.docker, item.agent_id, item.api_url, item.sk_value
    )

    if not success:
        raise fastapi.exceptions.HTTPException(
            status_code=400,
            detail=models.format_response(False, "fail to create agent"),
        )

    return models.format_response(True, "success")


@app.post(
    "/kill/", summary="销毁一个 Agent", description="通过 agent_id 停止并移除对应的容器"
)
async def kill_agent(item: models.KillRequest):
    success = await utils.kill_agent_instance(app.state.docker, item.agent_id)

    if not success:
        raise fastapi.exceptions.HTTPException(
            status_code=400, detail=models.format_response(False, "fail to kill agent")
        )

    return models.format_response(True, "success")


@app.post("/delete/", summary="删除 Agent", description="删除 Agent 及其对应的文件")
async def delete_agent(item: models.DeleteRequest):
    success = await utils.delete_agent_instance(app.state.docker, item.agent_id)

    if not success:
        raise fastapi.exceptions.HTTPException(
            status_code=400,
            detail=models.format_response(False, "fail to delete agent"),
        )

    return models.format_response(True, "success")


async def main():
    if not pathlib.Path("./INSTALLED").exists():
        await init.init()

    server_config = uvicorn.Config(app, host=config.HOST, port=config.PORT)
    server = uvicorn.Server(server_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
