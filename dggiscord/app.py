from threading import Thread

import helpers.log
import helpers.config as config
import helpers.database
import discord.client as client
import helpers.live
from helpers.livehandler import live_handler

import subsync.translator
import subsync.sync
import discord.background
import discord.memberstate
import discord.serverstate

import commands.sync
import commands.livestatuscfg

Thread(target=helpers.live.init, args=[live_handler]).start()
client.bot.run(config.cfg["discord"]["token"])
