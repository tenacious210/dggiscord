from threading import Thread

import helpers.log
import helpers.config as config
import helpers.database
import discord.client as client
import helpers.live
from helpers import livehandler, livenotifier

import subsync.translator
import subsync.sync
import discord.background
import discord.memberstate
import discord.serverstate

import commands.sync
import commands.livestatuscfg

livenotifier.init(client.bot)
livehandler.init(livenotifier.send_live_notification)
Thread(target=helpers.live.init, args=[livehandler.live_handler]).start()
client.bot.run(config.cfg["discord"]["token"])
