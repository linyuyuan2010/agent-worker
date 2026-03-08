import asyncio
import pathlib
import logging
import time
import shutil

import config

logger = logging.getLogger("agent_worker")


async def delete_expired_files():
    while True:
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
