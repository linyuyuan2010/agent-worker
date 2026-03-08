import pathlib

import aiodocker

client = aiodocker.Docker()

async def init(data:pathlib.Path=pathlib.Path('./data')):
    await client.networks.create({"Name": "agents-network", "Driver": "bridge"})
    data.mkdir(exist_ok=True, parents=True)
    pathlib.Path('./INSTALLED').touch()