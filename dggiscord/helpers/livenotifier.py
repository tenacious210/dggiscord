import sqlite3
import logging
from datetime import datetime
from dateutil.parser import isoparse
from time import mktime

from disnake.ext import commands

from helpers.config import cfg

logger = logging.getLogger(__name__)
logger.info("loading...")


def init(bot_to_use: commands.bot.Bot):
    global bot
    bot = bot_to_use


def send_live_notification(platform: str, streaminfo: dict):
    # Temporarily using this while working on supporting other streams
    # ----------------------------------------------------------------
    if not platform == "youtube":
        logger.info("Skipping non-youtube stream")
        return
    # ----------------------------------------------------------------

    con = sqlite3.connect(cfg["db"], detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    hubchannels_query = cur.execute("SELECT * FROM hubchannels").fetchall()
    hubchannels = [dict(channel) for channel in hubchannels_query]
    for hubchannel in hubchannels:
        last_notification_sent = isoparse(hubchannel["last_notification_sent"])
        cooldown = cfg["discord"]["live_notification_cooldown"]
        if (datetime.now() - last_notification_sent).seconds <= cooldown:
            logger.info(f"Live notification on cooldown for {hubchannel['hubchannel']}")
            continue

        notification = ""
        if hubchannel["role"]:
            notification += f"<@&{hubchannel['role']}> "

        notification += "Destiny went live "

        if time_started := streaminfo["started_at"]:
            time_started = isoparse(time_started)
            unix_time_started = mktime(time_started.timetuple())

            notification += f"<t:{round(unix_time_started)}:R>!"

        notification += "\n\n"

        if platform == "youtube":
            notification += f"https://www.youtube.com/watch?v={streaminfo['id']}"
        elif platform == "kick":
            notification += f"https://kick.com/{streaminfo['id']}"

        channel = bot.get_channel(hubchannel["hubchannel"])
        logger.info(f"Sending live notification to {channel.id}")
        bot.loop.create_task(channel.send(notification))

        cur.execute(
            "UPDATE hubchannels SET last_notification_sent = ? WHERE hubchannel = ?",
            (datetime.now().isoformat(), hubchannel["hubchannel"]),
        )
        con.commit()
