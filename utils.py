import logging
import pathlib
import shutil
import time

from aiodocker import Docker

import config

logger = logging.getLogger("agent_worker")
logger.setLevel(logging.DEBUG)


async def create_agent_instance(
    docker: Docker, agent_id: str, api_url: str, sk_value: str
):
    """创建容器"""
    data_dir = pathlib.Path(f"./data/{agent_id}")
    container_name = f"agent-{agent_id}"

    # 记录是否创建了目录，以便回滚
    dir_created = False
    container = None

    try:
        # 1. 原子化准备阶段
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
            dir_created = True

        container_config = {
            "Image": "openclaw/openclaw:latest",
            "name": container_name,
            "Env": [f"OPENCLAW_API_BASE={api_url}", f"OPENCLAW_API_KEY={sk_value}"],
            "HostConfig": {
                "NetworkMode": "agents-network",
                "Binds": [f"{data_dir.absolute()}:/app/data"],
            },
        }

        # 2. 执行操作
        container = await docker.containers.create(config=container_config)
        await container.start()

        return True, container

    except Exception as e:
        logger.error(f"Failed to create agent {agent_id}: {e}")

        # 3. 回滚逻辑
        if container:
            try:
                await container.delete(force=True)
            except:
                pass

        if dir_created:
            # 只有当是我们这次新创建的目录才删除，避免误删已有数据
            shutil.rmtree(data_dir, ignore_errors=True)

        return False, None


async def kill_agent_instance(docker: Docker, agent_id: str) -> bool:
    """杀死 agent"""

    try:
        container = docker.containers.container(f"agent-{agent_id}")
        await container.kill()
        logger.debug(f"Killed agent id {agent_id}")

        return True
    except Exception:
        return False


async def delete_agent_instance(docker: Docker, agent_id: str) -> bool:
    """删除 agent"""
    source = pathlib.Path(f"./data/{agent_id}")
    destination = pathlib.Path(
        f"./data/{agent_id}.DELETED.{int(time.time()) + config.EXPIRY}"
    )
    try:
        # 设置文件删除标志
        source.rename(destination)

        # 杀死容器
        container = docker.containers.container(f"agent-{agent_id}")
        await container.kill()

        logger.debug(f"Killed agent id {agent_id}")

        return True
    except:
        destination.rename(source)
        return False
