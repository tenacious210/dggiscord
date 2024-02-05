import logging
from typing import Callable

from dggbot import DGGLive, StreamInfo

logger = logging.getLogger(__name__)
logger.info("loading...")


live = DGGLive()


def init(handler: Callable):
    live.handler = handler
    live.run_forever()


@live.event()
def on_streaminfo(streaminfo: StreamInfo):
    logger.debug("Stream info received")
    live.handler(streaminfo)
