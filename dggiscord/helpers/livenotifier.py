import sqlite3
import logging
from datetime import datetime
from dateutil.parser import isoparse
from time import mktime, sleep

from disnake.ext import commands

from helpers.config import cfg

logger = logging.getLogger(__name__)
logger.info("loading...")

youtube_md_link = lambda vid_id: f"[YouTube](https://youtu.be/{vid_id})"
kick_md_link = lambda usr_id: f"[Kick](https://kick.com/{usr_id})"


def init(bot_to_use: commands.bot.Bot):
    global bot
    bot = bot_to_use


def parse_streams(streams: dict):
    example = {"started": {}, "ended": {}, "ongoing": {}, "offline": {}}

    con = sqlite3.connect(cfg["db"], detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    hubchannels_query = cur.execute("SELECT * FROM hubchannels").fetchall()
    hubchannels = [dict(channel) for channel in hubchannels_query]
    for hubchannel in hubchannels:
        notification = generate_live_notification(
            streams["ongoing"], hubchannel["role"]
        )
        channel = bot.get_channel(hubchannel["hubchannel"])
        last_notification_sent = isoparse(hubchannel["last_notification_sent"])
        cooldown = cfg["discord"]["live_notification_cooldown"]
        on_cooldown = (datetime.now() - last_notification_sent).seconds <= cooldown

        if (
            streams["started"]
            and not on_cooldown
            or hubchannel["last_notification_id"] is None
        ):
            logger.info("sending new notification")
            cur.execute(
                """UPDATE hubchannels 
                   SET last_notification_sent = ? 
                   WHERE hubchannel = ?""",
                (
                    datetime.now().isoformat(),
                    hubchannel["hubchannel"],
                ),
            )
            con.commit()
            sent_notification = bot.loop.create_task(channel.send(notification))
            while not sent_notification.done():
                sleep(0.1)
            cur.execute(
                """UPDATE hubchannels
                   SET last_notification_id = ?
                   WHERE hubchannel = ?""",
                (
                    sent_notification.result().id,
                    hubchannel["hubchannel"],
                ),
            )
            con.commit()
        elif (
            (streams["started"] or streams["ended"])
            and on_cooldown
            and hubchannel["last_notification_id"]
        ):
            logger.info("updating old notificaiton")
            last_notification = bot.get_message(hubchannel["last_notification_id"])
            bot.loop.create_task(last_notification.edit(notification))
        elif (
            "youtube" in streams["offline"].keys()
            and not streams["ongoing"]
            and hubchannel["last_notification_id"]
        ):
            notification = generate_offline_notification(streams["offline"]["youtube"])
            logger.info("updating old notification to offline notification")
            last_notification = bot.get_message(hubchannel["last_notification_id"])
            bot.loop.create_task(last_notification.edit(notification))
        else:
            logger.info("no new notifications to send")

    con.close()


def generate_live_notification(streams: dict, role: str = None) -> str:
    logger.debug("generating notification")
    notification = "**"
    if role:
        notification += f"<@&{role}> "

    notification += "Destiny went live"

    preferred_platform = None
    if "youtube" in streams.keys():
        preferred_platform = "youtube"
    elif "kick" in streams.keys():
        preferred_platform = "kick"

    if preferred_platform and (
        time_started := streams[preferred_platform]["started_at"]
    ):
        time_started = isoparse(time_started)
        unix_time_started = mktime(time_started.timetuple())
        notification += f" <t:{round(unix_time_started)}:R>"

    notification += "!**"

    notification += "\n**Streams:** "

    stream_links = []
    if "youtube" in streams.keys():
        stream_links.append(youtube_md_link(streams["youtube"]["id"]))
    if "kick" in streams.keys():
        stream_links.append(kick_md_link(streams["kick"]["id"]))

    notification += " | ".join(stream_links)
    logger.debug(f"notification:\n{notification}")
    return notification


def generate_offline_notification(yt_streaminfo: dict) -> str:
    logger.debug("generating offline notification")

    notification = "Destiny was live"
    if "ended_at" in yt_streaminfo:
        time_ended = isoparse(time_ended)
        unix_time_ended = mktime(time_ended.timetuple())
        notification += f" <t:{round(unix_time_ended)}:R>"

    notification += "\n\n Check the "
    notification += f"[Vods]({cfg['vodplaylist']})"

    logger.debug(f"offline notification:\n{notification}")
    return notification
