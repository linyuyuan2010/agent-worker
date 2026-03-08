import asyncio
import pathlib
import logging
import time
import shutil

import psutil
import httpx

import config

logger = logging.getLogger("agent_worker")


async def delete_expired_files():
    while True:
        try:
            logger.info("Deleting expired files")
            now = int(time.time())
            data = pathlib.Path("./data")

            if not data.is_dir():
                logger.warning("No data dir")
                break

            for folder in data.iterdir():
                if int(folder.name.split(".")[2]) <= now:
                    await asyncio.to_thread(shutil.rmtree, folder.absolute())

            await asyncio.sleep(float(config.CLEAR_EXPIRED_FILES_CRON))

        except asyncio.CancelledError:
            logger.info("Clear expired files task caneceled")
        except Exception as e:
            logger.error(f"Error on clearing files {e}")


async def check_worker_load(http_client: httpx.AsyncClient):
    while True:
        try:
            logger.info("Checking worker load")

            cpu = await asyncio.to_thread(psutil.cpu_percent, interval=1)
            mem = psutil.virtual_memory().percent
            load = await asyncio.to_thread(psutil.getloadavg)

            info = {
                "worker": config.WORKER_ID,
                "cpu": cpu,
                "mem": mem,
                "load": load,
            }

            await http_client.post(f"{config.CONTROL_PANEL}/worker-status/", json=info)

            await asyncio.sleep(float(config.CHECK_WORKER_LOAD_CRON))

        except asyncio.CancelledError:
            logger.info("Health check task caneceled")
        except Exception as e:
            logger.error(f"Error on uploading status {e}")
