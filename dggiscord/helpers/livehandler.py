import sqlite3
import logging
import dataclasses
from typing import Callable

from dggbot.live import StreamInfo
from dggbot.live.message import Stream

from helpers.config import cfg


logger = logging.getLogger(__name__)
logger.info("loading...")

sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

liveinfo_template = lambda: {
    "live": False,
    "type": None,
    "game": None,
    "preview": None,
    "status_text": None,
    "started_at": None,
    "ended_at": None,
    "duration": None,
    "viewers": None,
    "id": None,
    "chat_url": None,
}


def init(notify_func: Callable):
    global live_notify
    live_notify = notify_func


def live_handler(streaminfo: StreamInfo):
    logger.debug(f"Got stream info")

    con = sqlite3.connect(cfg["db"], detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    old_streaminfo = cur.execute("SELECT * FROM liveinfo").fetchall()
    old_streaminfo = [dict(stream) for stream in old_streaminfo]
    old_streaminfo = {stream.pop("platform"): stream for stream in old_streaminfo}

    new_streaminfo = dataclasses.asdict(streaminfo)
    for platform in new_streaminfo.keys():
        if new_streaminfo[platform] == None:
            new_streaminfo[platform] = liveinfo_template()

    streams = {"started": {}, "ended": {}, "ongoing": {}, "offline": {}}
    for platform in new_streaminfo.keys():
        if (
            old_streaminfo[platform]["live"] == False
            and new_streaminfo[platform]["live"] == True
        ):
            streams["started"][platform] = new_streaminfo[platform]

        if (
            old_streaminfo[platform]["live"] == True
            and new_streaminfo[platform]["live"] == False
        ):
            streams["ended"][platform] = new_streaminfo[platform]

        if new_streaminfo[platform]["live"] == True:
            streams["ongoing"][platform] = new_streaminfo[platform]
        elif new_streaminfo[platform] == False:
            streams["offline"][platform] = new_streaminfo[platform]

    logger.info(f"Live streams: {', '.join(streams['ongoing'].keys())}")
    live_notify(streams)

    for platform in new_streaminfo.keys():
        for k, v in new_streaminfo[platform].items():
            params = {"value": v, "platform": platform}
            # don't try this at home, kids
            query = f"UPDATE liveinfo SET {k} = :value WHERE platform = :platform"
            cur.execute(query, params)

    con.commit()
    con.close()
