import re
from datetime import datetime, timedelta

from helpers.log import logging
from helpers.database import con, cur
from helpers.config import cfg
import discord.client as client

logger = logging.getLogger(__name__)
logger.info("loading...")

ROLE_PATTERN = re.compile(r"<@&\d+>")


@client.bot.command()
async def hubchannel(ctx, arg: str, role: str = None):
    # only let server admins determine this
    permissions = ctx.message.channel.permissions_for(ctx.message.author)
    if not permissions.administrator:
        return

    if arg == "get":
        cur.execute(
            "SELECT * from hubchannels WHERE discord_server=?", (ctx.message.guild.id,)
        )
        row = cur.fetchone()

        logger.info(f"hubchannel get response from db {row}")
        await ctx.reply(f"Current hub channel is set to <#{row[1]}>")
    elif arg == "set":
        last_sent = datetime.now() - timedelta(
            seconds=cfg["discord"]["live_notification_cooldown"]
        )
        cur.execute(
            "REPLACE INTO hubchannels VALUES(?,?,?,?)",
            (ctx.message.guild.id, ctx.message.channel.id, None, last_sent.isoformat()),
        )
        con.commit()
        await ctx.reply(
            f"Channel set to <#{ctx.message.channel.id}>. (Optional: Add a role with `!hubchannel role @<role>`)"
        )
    elif arg == "role":
        if not ROLE_PATTERN.match(role):
            await ctx.reply('Error: Invalid argument for "role"')
            return
        role_num = int(role[3:-1])
        cur.execute(
            "UPDATE hubchannels SET (role) = (?) WHERE (discord_server=?)",
            (role_num, ctx.message.guild.id),
        )
        con.commit()
        await ctx.reply(f"Role for <#{ctx.message.channel.id}> set to {role}")

    else:
        await ctx.reply("Error: Command args `set|get|role`.")
