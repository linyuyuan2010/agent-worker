import pathlib
import os

import aiodocker

client = aiodocker.Docker()


async def init():

    data = pathlib.Path("./data")

    # 初始化持久卷
    base_path = pathlib.Path("./data")
    (pathlib.Path("./") / "lua").mkdir(parents=True, exist_ok=True)
    (base_path / "openresty" / "conf.d").mkdir(parents=True, exist_ok=True)
    (base_path / "openresty" / "logs").mkdir(parents=True, exist_ok=True)
    conf_file = base_path / "nginx.conf"
    if not conf_file.exists():
        conf_file.touch()
    (base_path / "redis_data").mkdir(parents=True, exist_ok=True)

    # 初始化网络
    await client.networks.create({"Name": "agents-network", "Driver": "bridge"})

    # 初始化
    openresty_path = pathlib.Path("./openresty").absolute()

    await client.containers.create(
        {
            "Image": "openresty/openresty:alpine",
            "name": "openresty",
            "HostConfig": {
                "NetworkMode": "agents-network",
                "Binds": [
                    f"{openresty_path}/nginx.conf:/usr/local/openresty/nginx/conf/nginx.conf:ro",
                    f"{openresty_path}/conf.d:/etc/nginx/conf.d:ro",
                    f"{openresty_path}/lua:/usr/local/openresty/lua:ro",
                    f"{openresty_path}/logs:/usr/local/openresty/nginx/logs:rw",
                ],
            },
        }
    )

    await client.containers.create(
        {
            "Image": "redis:latest",
            "name": "redis",
            "Cmd": ["redis-server", "--appendonly", "yes"],
            "HostConfig": {
                "NetworkMode": "agents-network",
                "Binds": [f"{base_path.absolute()}/redis_data:/data:rw"],
            },
        }
    )

    data.mkdir(exist_ok=True, parents=True)
    pathlib.Path("./INSTALLED").touch()
