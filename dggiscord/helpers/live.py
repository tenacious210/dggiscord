import logging
from typing import Callable

from dggbot import DGGLive, StreamInfo

logger = logging.getLogger(__name__)
logger.info("loading...")

# MONKEY PATCHES, DELETE AFTER FRITZ FIXES
# ----------------------------------------
import dataclasses
import dggbot.live


@dataclasses.dataclass
class Stream:
    live: bool
    game: str
    preview: str
    status_text: str
    started_at: str
    ended_at: str
    duration: int
    viewers: int
    id: str
    platform: str
    type: str
    chat_url: str

    @classmethod
    def from_json(cls, data: dict) -> "Stream":
        return cls(**data)


dggbot.live.message.Stream = Stream
DGGLive.__repr__ = lambda x: "hello"
# ----------------------------------------

live = DGGLive()


def init(handler: Callable):
    live.handler = handler
    live.run_forever()


@live.event()
def on_streaminfo(streaminfo: StreamInfo):
    logger.debug("Stream info received")
    live.handler(streaminfo)
