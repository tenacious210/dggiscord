from helpers.config import cfg
from helpers.log import logging
import sqlite3

logger = logging.getLogger(__name__)
logger.info("loading...")

try:
    con = sqlite3.connect(cfg["db"], detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    logger.info("sqlite database connection and cursor successfully initialized")
except Exception as e:
    logger.critical("sqlite database failed with error: {0}".format(e))
    exit()

# Check if the table exists, if not make the schema
cur.execute(
    "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='flairmap'"
)
if cur.fetchone()[0] == 0:
    logger.warn("table 'flairmap' does not exist in database, creating schema...")
    cur.execute(
        """CREATE TABLE 'flairmap' ( 
            `discord_server` INTEGER,
            `discord_role` INTEGER,
            `dgg_flair` TEXT,
            `last_updated` TEXT,
            `last_refresh` TEXT,
            PRIMARY KEY(`discord_role`) )"""
    )

# hubchannel configs
cur.execute(
    "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='hubchannels'"
)
if cur.fetchone()[0] == 0:
    logger.warn("table 'hubchannels' does not exist in database, creating schema...")
    cur.execute(
        """CREATE TABLE 'hubchannels' ( 
            `discord_server` INTEGER PRIMARY KEY,
            `hubchannel` INTEGER,
            `role` INTEGER,
            `last_notification_sent` TEXT,
            `last_notification_id` INTEGER )"""
    )
    cur.execute("CREATE UNIQUE INDEX idx_hubchannels ON hubchannels (discord_server)")

# livestream details
cur.execute(
    "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='liveinfo'"
)
if cur.fetchone()[0] == 0:
    logger.warn("table 'liveinfo' does not exist in database, creating schema...")
    cur.execute(
        """CREATE TABLE 'liveinfo' ( 
                `platform` TEXT UNIQUE, 
                `live` BOOLEAN NOT NULL,
                `type` TEXT, 
                `game` TEXT,
                `preview` TEXT,
                `status_text` TEXT,
                `started_at` TEXT,
                `ended_at` TEXT,
                `duration` INTEGER,
                `viewers` INTEGER,
                `id` TEXT,
                `chat_url` TEXT )"""
    )
    for platform in ("youtube", "kick", "twitch", "rumble", "facebook"):
        params = {"platform": platform}
        query = "INSERT INTO 'liveinfo' (platform, live) VALUES (:platform, FALSE)"
        cur.execute(query, params)
    con.commit()
