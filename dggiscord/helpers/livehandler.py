import sqlite3
import logging
import dataclasses

from dggbot.live import StreamInfo
from dggbot.live.message import Stream

from helpers.config import cfg


logger = logging.getLogger(__name__)
logger.info("loading...")

sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


def live_handler(streaminfo: StreamInfo):
    logger.info(f"Got stream info")

    con = sqlite3.connect(cfg["db"], detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    old_streams = cur.execute("SELECT * FROM liveinfo").fetchall()
    old_streams = [dict(stream) for stream in old_streams]
    old_streams = {stream.pop("platform"): stream for stream in old_streams}

    new_streams = streaminfo.get_livestreams()
    new_streams = [dataclasses.asdict(stream) for stream in new_streams]
    new_streams = {stream.pop("platform"): stream for stream in new_streams}

    # compare them and send a notification if they're different

    for platform in new_streams.keys():
        for k, v in new_streams[platform].items():
            params = {"value": v, "platform": platform}
            # don't try this at home, kids
            query = f"UPDATE liveinfo SET {k} = :value WHERE platform = :platform"
            cur.execute(query, params)

    con.commit()
